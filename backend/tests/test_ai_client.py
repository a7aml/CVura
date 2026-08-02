from unittest.mock import AsyncMock, patch

import httpx
import openai
import pytest

from app.ai import client as ai_client
from app.schemas.job import MAX_RAW_DESCRIPTION_LENGTH


def _connection_error() -> openai.APIConnectionError:
    return openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))


def _rate_limit_error() -> openai.RateLimitError:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(status_code=429, request=request)
    return openai.RateLimitError("rate limited", response=response, body=None)


@patch("app.ai.client._client")
async def test_analyze_job_description_wraps_connection_error(mock_client):
    mock_client.responses.parse = AsyncMock(side_effect=_connection_error())

    with pytest.raises(ai_client.AIProviderError):
        await ai_client.analyze_job_description("some jd")


@patch("app.ai.client._client")
async def test_analyze_job_description_wraps_rate_limit_error(mock_client):
    mock_client.responses.parse = AsyncMock(side_effect=_rate_limit_error())

    with pytest.raises(ai_client.AIProviderError):
        await ai_client.analyze_job_description("some jd")


@patch("app.ai.client._client")
async def test_analyze_job_description_raises_invalid_on_empty_parsed_output(mock_client):
    mock_client.responses.parse = AsyncMock(return_value=AsyncMock(output_parsed=None, status="incomplete"))

    with pytest.raises(ai_client.AIResponseInvalid):
        await ai_client.analyze_job_description("some jd")


@patch("app.ai.client._client")
async def test_analyze_job_description_rejects_oversized_input_before_calling_api(mock_client):
    mock_client.responses.parse = AsyncMock()
    oversized = "x" * (MAX_RAW_DESCRIPTION_LENGTH + 1)

    with pytest.raises(ai_client.RawDescriptionTooLong):
        await ai_client.analyze_job_description(oversized)

    mock_client.responses.parse.assert_not_awaited()


@patch("app.ai.client._client")
async def test_analyze_job_description_allows_input_at_the_limit(mock_client):
    mock_client.responses.parse = AsyncMock(return_value=AsyncMock(output_parsed="ok", status="completed"))
    at_limit = "x" * MAX_RAW_DESCRIPTION_LENGTH

    result = await ai_client.analyze_job_description(at_limit)

    assert result == "ok"
    mock_client.responses.parse.assert_awaited_once()


_JD_CONTEXT = {"title": "Backend Engineer", "seniority": "mid", "required_skills": ["Python"]}


@patch("app.ai.client._client")
async def test_tailor_resume_wraps_connection_error(mock_client):
    mock_client.responses.parse = AsyncMock(side_effect=_connection_error())

    with pytest.raises(ai_client.AIProviderError):
        await ai_client.tailor_resume(["Python"], [], [], _JD_CONTEXT)


@patch("app.ai.client._client")
async def test_tailor_resume_wraps_rate_limit_error(mock_client):
    mock_client.responses.parse = AsyncMock(side_effect=_rate_limit_error())

    with pytest.raises(ai_client.AIProviderError):
        await ai_client.tailor_resume(["Python"], [], [], _JD_CONTEXT)


@patch("app.ai.client._client")
async def test_tailor_resume_raises_invalid_on_empty_parsed_output(mock_client):
    mock_client.responses.parse = AsyncMock(return_value=AsyncMock(output_parsed=None, status="incomplete"))

    with pytest.raises(ai_client.AIResponseInvalid):
        await ai_client.tailor_resume(["Python"], [], [], _JD_CONTEXT)


@patch("app.ai.client._client")
async def test_tailor_resume_rejects_oversized_input_before_calling_api(mock_client):
    mock_client.responses.parse = AsyncMock()
    oversized_skills = ["x" * ai_client.MAX_TAILOR_INPUT_LENGTH]

    with pytest.raises(ai_client.TailorInputTooLarge):
        await ai_client.tailor_resume(oversized_skills, [], [], _JD_CONTEXT)

    mock_client.responses.parse.assert_not_awaited()


@patch("app.ai.client._client")
async def test_tailor_resume_returns_parsed_output_on_success(mock_client):
    mock_client.responses.parse = AsyncMock(return_value=AsyncMock(output_parsed="ok", status="completed"))

    result = await ai_client.tailor_resume(["Python"], [], [], _JD_CONTEXT)

    assert result == "ok"
    mock_client.responses.parse.assert_awaited_once()
