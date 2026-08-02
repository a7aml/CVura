import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.ai.client import AIProviderError, AIResponseInvalid, RawDescriptionTooLong
from app.schemas.job import JobAnalysis
from app.services import job_analysis_service


class FakeJob:
    def __init__(self, user_id, title="Senior Product Designer", raw_description="...", parsed_json=None):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.title = title
        self.raw_description = raw_description
        self.parsed_json = parsed_json


@patch("app.services.job_analysis_service.job_repo")
async def test_create_job(mock_repo):
    user_id = uuid.uuid4()
    created = FakeJob(user_id)
    mock_repo.create_job = AsyncMock(return_value=created)

    data = {"source": "linkedin", "title": "Senior Product Designer", "raw_description": "..."}
    result = await job_analysis_service.create_job(None, user_id, data)

    assert result is created
    mock_repo.create_job.assert_awaited_once_with(None, user_id, **data)


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_success(mock_repo):
    user_id = uuid.uuid4()
    existing = FakeJob(user_id)
    mock_repo.get_by_id = AsyncMock(return_value=existing)

    result = await job_analysis_service.get_job(None, user_id, existing.id)
    assert result is existing


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_missing_raises(mock_repo):
    mock_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(job_analysis_service.JobNotFound):
        await job_analysis_service.get_job(None, uuid.uuid4(), uuid.uuid4())


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_owned_by_another_user_raises(mock_repo):
    other_users_job = FakeJob(uuid.uuid4())
    mock_repo.get_by_id = AsyncMock(return_value=other_users_job)

    with pytest.raises(job_analysis_service.JobNotFound):
        await job_analysis_service.get_job(None, uuid.uuid4(), other_users_job.id)


@patch("app.services.job_analysis_service.job_repo")
async def test_list_jobs(mock_repo):
    user_id = uuid.uuid4()
    jobs = [FakeJob(user_id), FakeJob(user_id)]
    mock_repo.list_by_user = AsyncMock(return_value=jobs)

    result = await job_analysis_service.list_jobs(None, user_id)
    assert result is jobs


SAMPLE_ANALYSIS = JobAnalysis(
    required_skills=["Python"],
    preferred_skills=["Kafka"],
    technologies=["Python", "PostgreSQL"],
    seniority="mid",
    responsibilities=["Build things"],
    keywords_ats=["Python"],
)


@patch("app.ai.client.analyze_job_description")
@patch("app.services.job_analysis_service.job_repo")
async def test_analyze_job_reuses_cached_analysis_without_calling_ai(mock_repo, mock_ai):
    user_id = uuid.uuid4()
    job = FakeJob(user_id, raw_description="same jd text")
    cached = FakeJob(user_id, raw_description="same jd text", parsed_json={"seniority": "senior"})
    mock_repo.get_by_id = AsyncMock(return_value=job)
    mock_repo.get_analyzed_by_hash = AsyncMock(return_value=cached)
    mock_repo.set_analysis = AsyncMock(return_value=job)

    result = await job_analysis_service.analyze_job(None, user_id, job.id)

    assert result is job
    mock_ai.assert_not_awaited()
    mock_repo.set_analysis.assert_awaited_once()
    assert mock_repo.set_analysis.call_args.args[2] == {"seniority": "senior"}


@patch("app.ai.client.analyze_job_description")
@patch("app.services.job_analysis_service.job_repo")
async def test_analyze_job_calls_ai_on_cache_miss_and_saves_result(mock_repo, mock_ai):
    user_id = uuid.uuid4()
    job = FakeJob(user_id, raw_description="new jd text")
    mock_repo.get_by_id = AsyncMock(return_value=job)
    mock_repo.get_analyzed_by_hash = AsyncMock(return_value=None)
    mock_repo.set_analysis = AsyncMock(return_value=job)
    mock_ai.return_value = SAMPLE_ANALYSIS

    result = await job_analysis_service.analyze_job(None, user_id, job.id)

    assert result is job
    mock_ai.assert_awaited_once_with("new jd text")
    mock_repo.set_analysis.assert_awaited_once()
    assert mock_repo.set_analysis.call_args.args[2] == SAMPLE_ANALYSIS.model_dump()


@patch("app.ai.client.analyze_job_description")
async def test_analyze_with_retry_succeeds_on_second_attempt(mock_ai):
    mock_ai.side_effect = [AIResponseInvalid("bad output"), SAMPLE_ANALYSIS]

    result = await job_analysis_service._analyze_with_retry("some jd")

    assert result is SAMPLE_ANALYSIS
    assert mock_ai.await_count == 2


@patch("app.ai.client.analyze_job_description")
async def test_analyze_with_retry_raises_after_two_failures(mock_ai):
    mock_ai.side_effect = AIResponseInvalid("bad output")

    with pytest.raises(job_analysis_service.JobAnalysisError):
        await job_analysis_service._analyze_with_retry("some jd")

    assert mock_ai.await_count == 2


@patch("app.services.job_analysis_service.job_repo")
async def test_analyze_job_missing_job_raises_not_found(mock_repo):
    mock_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(job_analysis_service.JobNotFound):
        await job_analysis_service.analyze_job(None, uuid.uuid4(), uuid.uuid4())


@patch("app.ai.client.analyze_job_description")
async def test_analyze_with_retry_recovers_from_transient_provider_error(mock_ai):
    mock_ai.side_effect = [AIProviderError("connection reset"), SAMPLE_ANALYSIS]

    result = await job_analysis_service._analyze_with_retry("some jd")

    assert result is SAMPLE_ANALYSIS
    assert mock_ai.await_count == 2


@patch("app.ai.client.analyze_job_description")
async def test_analyze_with_retry_raises_service_unavailable_after_two_provider_failures(mock_ai):
    mock_ai.side_effect = AIProviderError("connection reset")

    with pytest.raises(job_analysis_service.AIServiceUnavailable):
        await job_analysis_service._analyze_with_retry("some jd")

    assert mock_ai.await_count == 2


@patch("app.ai.client.analyze_job_description")
@patch("app.services.job_analysis_service.job_repo")
async def test_analyze_job_rejects_oversized_description_without_calling_ai_twice(mock_repo, mock_ai):
    user_id = uuid.uuid4()
    job = FakeJob(user_id, raw_description="x" * 100_000)
    mock_repo.get_by_id = AsyncMock(return_value=job)
    mock_repo.get_analyzed_by_hash = AsyncMock(return_value=None)
    mock_ai.side_effect = RawDescriptionTooLong("too long")

    with pytest.raises(job_analysis_service.JobDescriptionTooLong):
        await job_analysis_service.analyze_job(None, user_id, job.id)

    mock_ai.assert_awaited_once()
    mock_repo.set_analysis.assert_not_called()
