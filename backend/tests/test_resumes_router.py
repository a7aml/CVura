import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.deps import get_current_user, get_db
from app.core.security import limiter
from app.main import app
from app.models.job import Job
from app.models.user import User
from app.repositories import job_repo, user_repo
from app.schemas.resume import ExperienceEntry, ResumeTailorOutput
from app.services import job_analysis_service, resume_tailor_service


class FakeUser:
    def __init__(self):
        self.id = uuid.uuid4()


class FakeResume:
    def __init__(self, pdf_key=None):
        self.id = uuid.uuid4()
        self.version = 1
        self.pdf_key = pdf_key


SAMPLE_OUTPUT = ResumeTailorOutput(
    summary="Experienced backend engineer.",
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
    match_explanation="Strong Python and API overlap.",
)


@pytest.fixture
def client():
    fake_user = FakeUser()
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: None
    limiter.reset()
    yield TestClient(app), fake_user
    app.dependency_overrides.clear()


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_happy_path(mock_tailor, client):
    http_client, _ = client
    fake_resume = FakeResume()
    mock_tailor.return_value = (SAMPLE_OUTPUT, fake_resume)

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == str(fake_resume.id)
    assert body["version"] == 1
    assert body["summary"] == SAMPLE_OUTPUT.summary
    assert body["match_explanation"] == SAMPLE_OUTPUT.match_explanation


@patch("app.routers.resumes.pdf_service.generate_presigned_url")
@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_response_includes_presigned_pdf_url_on_success(mock_tailor, mock_presign, client):
    http_client, _ = client
    fake_resume = FakeResume(pdf_key="resumes/u1/r1.pdf")
    mock_tailor.return_value = (SAMPLE_OUTPUT, fake_resume)
    mock_presign.return_value = "https://r2.example.com/resumes/u1/r1.pdf?signature=abc"

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 200
    assert response.json()["pdf_url"] == "https://r2.example.com/resumes/u1/r1.pdf?signature=abc"
    mock_presign.assert_called_once_with("resumes/u1/r1.pdf")


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_returns_200_with_null_pdf_url_when_pdf_generation_fails(mock_tailor, client):
    """PDF generation failing (Typst compile error, R2 outage, etc.) must
    not fail the request — the tailored JSON is still valid."""
    http_client, _ = client
    fake_resume = FakeResume(pdf_key=None)
    mock_tailor.return_value = (SAMPLE_OUTPUT, fake_resume)

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 200
    body = response.json()
    assert body["pdf_url"] is None
    assert body["summary"] == SAMPLE_OUTPUT.summary


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_rejects_job_not_owned_by_user(mock_tailor, client):
    http_client, _ = client
    mock_tailor.side_effect = job_analysis_service.JobNotFound()

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 404


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_returns_404_when_profile_missing(mock_tailor, client):
    http_client, _ = client
    mock_tailor.side_effect = resume_tailor_service.ProfileNotFound()

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 404


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_returns_422_when_job_not_analyzed(mock_tailor, client):
    http_client, _ = client
    mock_tailor.side_effect = resume_tailor_service.JobNotAnalyzed()

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 422


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_returns_503_on_ai_provider_error(mock_tailor, client):
    http_client, _ = client
    mock_tailor.side_effect = resume_tailor_service.AIServiceUnavailable("AI provider is down")

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 503


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_returns_422_on_malformed_ai_output(mock_tailor, client):
    http_client, _ = client
    mock_tailor.side_effect = resume_tailor_service.ResumeTailorError("bad output twice")

    response = http_client.post(f"/jobs/{uuid.uuid4()}/tailor")

    assert response.status_code == 422


@patch("app.routers.resumes.resume_tailor_service.tailor_resume")
def test_tailor_resume_rate_limited_after_ten_requests_per_minute(mock_tailor, client):
    # Uses a different job_id per call on purpose: the limit must apply per
    # user across all their requests to this endpoint, not per URL (which
    # would let a caller bypass it just by rotating job_id).
    http_client, _ = client
    mock_tailor.return_value = (SAMPLE_OUTPUT, FakeResume())

    responses = [http_client.post(f"/jobs/{uuid.uuid4()}/tailor") for _ in range(11)]

    assert [r.status_code for r in responses[:10]] == [200] * 10
    assert responses[10].status_code == 429


async def test_tailor_resume_rejects_job_owned_by_another_user_end_to_end(db_session):
    """Real DB, real service, no mocks: get_job's ownership check rejects
    the job before any profile lookup or AI call is ever made."""
    owner_email = f"test-{uuid.uuid4()}@example.com"
    attacker_email = f"test-{uuid.uuid4()}@example.com"
    owner = await user_repo.create_local_user(db_session, owner_email, "hash")
    attacker = await user_repo.create_local_user(db_session, attacker_email, "hash")
    try:
        job = await job_repo.create_job(
            db_session, owner.id, source="linkedin", title="Owner's job", company=None, raw_description="x"
        )
        # get_db is deliberately left un-overridden — see test_jobs_router.py
        # for why (cross-event-loop asyncpg session reuse is unsafe here).
        app.dependency_overrides[get_current_user] = lambda: attacker
        limiter.reset()

        response = TestClient(app).post(f"/jobs/{job.id}/tailor")

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
        await db_session.execute(delete(Job).where(Job.user_id == owner.id))
        await db_session.execute(delete(User).where(User.id.in_([owner.id, attacker.id])))
        await db_session.commit()
