"""AI model calls, isolated from services logic."""

import asyncio
import contextlib
import json

import openai
from openai import AsyncOpenAI

from app.ai.prompts import (
    JOB_ANALYSIS_SYSTEM_PROMPT,
    PROFILE_EXTRACTION_SYSTEM_PROMPT,
    RESUME_TAILOR_SYSTEM_PROMPT,
    build_job_analysis_messages,
    build_profile_extraction_messages,
    build_resume_tailor_messages,
)
from app.core.config import settings
from app.schemas.job import MAX_RAW_DESCRIPTION_LENGTH, JobAnalysis
from app.schemas.profile_import import MAX_RESUME_TEXT_LENGTH, ProfileExtractionOutput
from app.schemas.resume import ResumeTailorOutput

_MODEL = "gpt-5.4-mini"
_MAX_OUTPUT_TOKENS = 2048
_TEMPERATURE = 0.2

# Same purpose as MAX_RAW_DESCRIPTION_LENGTH for job analysis: a generous cap
# on the serialized candidate-selection payload, well below anything needed
# for a real resume, to bound AI-provider cost/abuse.
MAX_TAILOR_INPUT_LENGTH = 20_000

# Transient failures worth retrying — a bad API key or a malformed request
# (auth/4xx errors) would fail identically on retry, so those are excluded.
_TRANSIENT_PROVIDER_ERRORS = (
    openai.RateLimitError,
    openai.APIConnectionError,  # also covers the APITimeoutError subclass
    openai.InternalServerError,
)

_client = AsyncOpenAI(api_key=settings.ai_api_key)

# Per-user rate limits (see security.py) cap *cost per user* but not how many
# AI calls run at once *across* users — a burst of legitimate concurrent
# requests could otherwise open unbounded simultaneous connections to the
# provider. This process runs a single uvicorn worker (see Dockerfile), so
# the limit is sized as a conservative, single-process budget rather than
# tuned to any particular provider rate tier.
_AI_CALL_CONCURRENCY_LIMIT = 8
_AI_CALL_QUEUE_TIMEOUT_SECONDS = 10.0
_ai_call_semaphore = asyncio.Semaphore(_AI_CALL_CONCURRENCY_LIMIT)


@contextlib.asynccontextmanager
async def _ai_call_slot():
    """Bounds concurrent in-flight AI calls process-wide. A caller that can't
    get a slot within the timeout fails fast instead of queuing indefinitely
    behind an unbounded backlog."""
    try:
        await asyncio.wait_for(_ai_call_semaphore.acquire(), timeout=_AI_CALL_QUEUE_TIMEOUT_SECONDS)
    except TimeoutError:
        raise AIProviderError("AI service is at capacity, please try again shortly") from None
    try:
        yield
    finally:
        _ai_call_semaphore.release()


class AIResponseInvalid(Exception):
    """The model did not return a response conforming to the requested schema."""


class AIProviderError(Exception):
    """The AI provider was unreachable, timed out, rate-limited, or errored."""


class RawDescriptionTooLong(Exception):
    """The job description exceeds the maximum length accepted for analysis."""


class TailorInputTooLarge(Exception):
    """The selected candidate subset exceeds the maximum size accepted for tailoring."""


class ResumeTextTooLong(Exception):
    """The extracted resume text exceeds the maximum length accepted for profile extraction."""


async def analyze_job_description(raw_description: str) -> JobAnalysis:
    if len(raw_description) > MAX_RAW_DESCRIPTION_LENGTH:
        raise RawDescriptionTooLong(
            f"raw_description is {len(raw_description)} characters, "
            f"exceeding the {MAX_RAW_DESCRIPTION_LENGTH}-character limit"
        )

    try:
        async with _ai_call_slot():
            response = await _client.responses.parse(
                model=_MODEL,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                temperature=_TEMPERATURE,
                instructions=JOB_ANALYSIS_SYSTEM_PROMPT,
                input=build_job_analysis_messages(raw_description),
                text_format=JobAnalysis,
            )
    except _TRANSIENT_PROVIDER_ERRORS as exc:
        raise AIProviderError(str(exc)) from exc

    if response.output_parsed is None:
        raise AIResponseInvalid(f"model returned no parsed output (status={response.status})")
    return response.output_parsed


async def extract_profile_from_resume(resume_text: str) -> ProfileExtractionOutput:
    if len(resume_text) > MAX_RESUME_TEXT_LENGTH:
        raise ResumeTextTooLong(
            f"resume text is {len(resume_text)} characters, exceeding the {MAX_RESUME_TEXT_LENGTH}-character limit"
        )

    try:
        async with _ai_call_slot():
            response = await _client.responses.parse(
                model=_MODEL,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                temperature=_TEMPERATURE,
                instructions=PROFILE_EXTRACTION_SYSTEM_PROMPT,
                input=build_profile_extraction_messages(resume_text),
                text_format=ProfileExtractionOutput,
            )
    except _TRANSIENT_PROVIDER_ERRORS as exc:
        raise AIProviderError(str(exc)) from exc

    if response.output_parsed is None:
        raise AIResponseInvalid(f"model returned no parsed output (status={response.status})")
    return response.output_parsed


async def tailor_resume(
    candidate_skills: list[str],
    candidate_experience: list[dict],
    candidate_projects: list[dict],
    jd_context: dict,
) -> ResumeTailorOutput:
    messages = build_resume_tailor_messages(candidate_skills, candidate_experience, candidate_projects, jd_context)
    input_length = len(json.dumps(messages, default=str))
    if input_length > MAX_TAILOR_INPUT_LENGTH:
        raise TailorInputTooLarge(
            f"tailor input is {input_length} characters, exceeding the {MAX_TAILOR_INPUT_LENGTH}-character limit"
        )

    try:
        async with _ai_call_slot():
            response = await _client.responses.parse(
                model=_MODEL,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                temperature=_TEMPERATURE,
                instructions=RESUME_TAILOR_SYSTEM_PROMPT,
                input=messages,
                text_format=ResumeTailorOutput,
            )
    except _TRANSIENT_PROVIDER_ERRORS as exc:
        raise AIProviderError(str(exc)) from exc

    if response.output_parsed is None:
        raise AIResponseInvalid(f"model returned no parsed output (status={response.status})")
    return response.output_parsed
