"""AI model calls, isolated from services logic."""

from openai import AsyncOpenAI

from app.ai.prompts import JOB_ANALYSIS_SYSTEM_PROMPT, build_job_analysis_messages
from app.core.config import settings
from app.schemas.job import JobAnalysis

_MODEL = "gpt-5.4-mini"
_MAX_OUTPUT_TOKENS = 2048
_TEMPERATURE = 0.2

_client = AsyncOpenAI(api_key=settings.ai_api_key)


class AIResponseInvalid(Exception):
    """The model did not return a response conforming to the requested schema."""


async def analyze_job_description(raw_description: str) -> JobAnalysis:
    response = await _client.responses.parse(
        model=_MODEL,
        max_output_tokens=_MAX_OUTPUT_TOKENS,
        temperature=_TEMPERATURE,
        instructions=JOB_ANALYSIS_SYSTEM_PROMPT,
        input=build_job_analysis_messages(raw_description),
        text_format=JobAnalysis,
    )
    if response.output_parsed is None:
        raise AIResponseInvalid(f"model returned no parsed output (status={response.status})")
    return response.output_parsed
