import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.resume import ExperienceEntry, ResumeTailorOutput
from app.services import job_analysis_service, resume_tailor_service


def _skill(name):
    return SimpleNamespace(name=name)


def _experience(title, company, bullets, start_date=None, end_date=None):
    return SimpleNamespace(
        id=uuid.uuid4(), title=title, company=company, bullets=bullets, start_date=start_date, end_date=end_date
    )


def _project(name, description="", tech_stack=None):
    return SimpleNamespace(id=uuid.uuid4(), name=name, description=description, tech_stack=tech_stack or [])


def _profile(skills=None, experiences=None, projects=None):
    return SimpleNamespace(skills=skills or [], experiences=experiences or [], projects=projects or [])


def _job(title="Backend Engineer", parsed_json=None):
    return SimpleNamespace(id=uuid.uuid4(), title=title, parsed_json=parsed_json)


SAMPLE_OUTPUT = ResumeTailorOutput(
    summary="Tailored summary",
    skills=["Python"],
    experience=[
        ExperienceEntry(
            source_experience_id=uuid.uuid4(),
            company="Acme",
            title="Backend Engineer",
            bullets=["Built REST APIs in Python"],
        )
    ],
    projects=[],
    match_explanation="Strong overlap on Python and REST APIs.",
)


@patch("app.services.resume_tailor_service.resume_repo")
@patch("app.services.resume_tailor_service.ai_client")
@patch("app.services.resume_tailor_service.profile_repo")
@patch("app.services.resume_tailor_service.job_analysis_service")
async def test_tailor_resume_happy_path(mock_jobs, mock_profile_repo, mock_ai, mock_resume_repo):
    user_id = uuid.uuid4()
    experience = _experience("Backend Engineer", "Acme", ["Built REST APIs in Python"], date(2022, 1, 1), None)
    profile = _profile(skills=[_skill("Python")], experiences=[experience])
    job = _job(parsed_json={"required_skills": ["Python"], "technologies": [], "keywords_ats": [], "preferred_skills": []})

    mock_jobs.get_job = AsyncMock(return_value=job)
    mock_jobs.JobNotFound = job_analysis_service.JobNotFound
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=profile)
    mock_ai.tailor_resume = AsyncMock(return_value=SAMPLE_OUTPUT)
    mock_ai.AIResponseInvalid = Exception
    mock_ai.AIProviderError = Exception
    mock_ai.TailorInputTooLarge = Exception
    fake_resume = SimpleNamespace(id=uuid.uuid4(), version=1)
    mock_resume_repo.create_resume = AsyncMock(return_value=fake_resume)

    tailored, resume = await resume_tailor_service.tailor_resume(None, user_id, job.id)

    assert tailored is SAMPLE_OUTPUT
    assert resume is fake_resume
    mock_ai.tailor_resume.assert_awaited_once()
    call_args = mock_ai.tailor_resume.await_args.args
    assert call_args[0] == ["Python"]
    mock_resume_repo.create_resume.assert_awaited_once_with(
        None, user_id, job.id, SAMPLE_OUTPUT.model_dump(mode="json"), SAMPLE_OUTPUT.match_explanation
    )


@patch("app.services.resume_tailor_service.profile_repo")
@patch("app.services.resume_tailor_service.job_analysis_service")
async def test_tailor_resume_raises_job_not_analyzed(mock_jobs, mock_profile_repo):
    job = _job(parsed_json=None)
    mock_jobs.get_job = AsyncMock(return_value=job)

    with pytest.raises(resume_tailor_service.JobNotAnalyzed):
        await resume_tailor_service.tailor_resume(None, uuid.uuid4(), job.id)

    mock_profile_repo.get_by_user_id.assert_not_called()


@patch("app.services.resume_tailor_service.profile_repo")
@patch("app.services.resume_tailor_service.job_analysis_service")
async def test_tailor_resume_raises_profile_not_found(mock_jobs, mock_profile_repo):
    job = _job(parsed_json={"required_skills": []})
    mock_jobs.get_job = AsyncMock(return_value=job)
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=None)

    with pytest.raises(resume_tailor_service.ProfileNotFound):
        await resume_tailor_service.tailor_resume(None, uuid.uuid4(), job.id)


@patch("app.services.resume_tailor_service.job_analysis_service")
async def test_tailor_resume_propagates_job_not_found_for_ownership_check(mock_jobs):
    mock_jobs.get_job = AsyncMock(side_effect=job_analysis_service.JobNotFound())

    with pytest.raises(job_analysis_service.JobNotFound):
        await resume_tailor_service.tailor_resume(None, uuid.uuid4(), uuid.uuid4())


@patch("app.services.resume_tailor_service.ai_client")
async def test_tailor_with_retry_succeeds_on_second_attempt(mock_ai):
    mock_ai.AIResponseInvalid = ValueError
    mock_ai.AIProviderError = ConnectionError
    mock_ai.tailor_resume = AsyncMock(side_effect=[ValueError("bad output"), SAMPLE_OUTPUT])

    result = await resume_tailor_service._tailor_with_retry(["Python"], [], [], {})

    assert result is SAMPLE_OUTPUT
    assert mock_ai.tailor_resume.await_count == 2


@patch("app.services.resume_tailor_service.ai_client")
async def test_tailor_with_retry_raises_resume_tailor_error_after_two_failures(mock_ai):
    mock_ai.AIResponseInvalid = ValueError
    mock_ai.AIProviderError = ConnectionError
    mock_ai.tailor_resume = AsyncMock(side_effect=ValueError("bad output"))

    with pytest.raises(resume_tailor_service.ResumeTailorError):
        await resume_tailor_service._tailor_with_retry(["Python"], [], [], {})

    assert mock_ai.tailor_resume.await_count == 2


@patch("app.services.resume_tailor_service.ai_client")
async def test_tailor_with_retry_raises_service_unavailable_after_two_provider_failures(mock_ai):
    mock_ai.AIResponseInvalid = ValueError
    mock_ai.AIProviderError = ConnectionError
    mock_ai.tailor_resume = AsyncMock(side_effect=ConnectionError("connection reset"))

    with pytest.raises(resume_tailor_service.AIServiceUnavailable):
        await resume_tailor_service._tailor_with_retry(["Python"], [], [], {})

    assert mock_ai.tailor_resume.await_count == 2


@patch("app.services.resume_tailor_service.resume_repo")
@patch("app.services.resume_tailor_service.ai_client")
@patch("app.services.resume_tailor_service.profile_repo")
@patch("app.services.resume_tailor_service.job_analysis_service")
async def test_tailor_resume_wraps_oversized_input_error(mock_jobs, mock_profile_repo, mock_ai, mock_resume_repo):
    job = _job(parsed_json={"required_skills": [], "technologies": [], "keywords_ats": [], "preferred_skills": []})
    mock_jobs.get_job = AsyncMock(return_value=job)
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=_profile())

    class TailorInputTooLarge(Exception):
        pass

    mock_ai.TailorInputTooLarge = TailorInputTooLarge
    mock_ai.AIResponseInvalid = ValueError
    mock_ai.AIProviderError = ConnectionError
    mock_ai.tailor_resume = AsyncMock(side_effect=TailorInputTooLarge("too big"))

    with pytest.raises(resume_tailor_service.TailorInputTooLarge):
        await resume_tailor_service.tailor_resume(None, uuid.uuid4(), job.id)

    mock_resume_repo.create_resume.assert_not_called()
