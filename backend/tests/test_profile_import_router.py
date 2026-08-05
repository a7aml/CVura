import datetime as dt
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
import typst
from fastapi.testclient import TestClient

from app.ai import client as ai_client
from app.core.deps import get_current_user, get_db
from app.core.security import limiter
from app.main import app
from app.schemas.profile import EducationIn
from app.schemas.profile_import import MAX_UPLOAD_SIZE_BYTES, PersonalInfoExtract, ProfileExtractionOutput
from app.services import profile_service


def _real_pdf_bytes(text: str) -> bytes:
    with tempfile.TemporaryDirectory() as tmpdir:
        typ_path = Path(tmpdir) / "doc.typ"
        typ_path.write_text(text, encoding="utf-8")
        return typst.compile(str(typ_path))


VALID_PDF = _real_pdf_bytes("Jordan Diaz\nSoftware Engineer with 5 years of experience at Acme Corp.")

FAKE_PROFILE_OUT = {
    "id": uuid.uuid4(),
    "user_id": uuid.uuid4(),
    "full_name": "Jordan Diaz",
    "phone": None,
    "location": None,
    "linkedin_url": None,
    "github_url": None,
    "portfolio_url": None,
    "desired_title": None,
    "summary": None,
    "career_objective": None,
    "created_at": dt.datetime.now(dt.timezone.utc),
    "updated_at": dt.datetime.now(dt.timezone.utc),
}


class FakeUser:
    def __init__(self):
        self.id = uuid.uuid4()


@pytest.fixture
def client():
    fake_user = FakeUser()
    # All repo/service calls in these tests are mocked, but the service layer
    # now calls db.commit()/db.rollback() itself around the save, so the
    # dependency-injected "db" needs to respond to those (a bare None can't).
    app.dependency_overrides[get_current_user] = lambda: fake_user
    app.dependency_overrides[get_db] = lambda: AsyncMock(name="db")
    limiter.reset()
    yield TestClient(app), fake_user
    app.dependency_overrides.clear()


class FakeExistingProfile:
    """Stands in for the SQLAlchemy Profile object get_full_profile returns:
    has one stale education item, so a replace's clear-then-save behavior
    can be asserted at the router level too."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.education = [SimpleNamespace(id=uuid.uuid4())]
        self.experiences = []
        self.projects = []
        self.skills = []
        self.certifications = []
        self.languages = []
        self.awards = []


def _upload(http_client, filename="resume.pdf", content=VALID_PDF, content_type="application/pdf", replace_existing=None):
    data = {} if replace_existing is None else {"replace_existing": str(replace_existing).lower()}
    return http_client.post("/profile/import-resume", files={"file": (filename, content, content_type)}, data=data)


@patch("app.services.profile_import_service.education_repo.create_many", new_callable=AsyncMock)
@patch("app.services.profile_import_service.profile_service.create_profile", new_callable=AsyncMock)
@patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock)
@patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock)
def test_import_resume_happy_path_saves_profile(mock_extract, mock_get, mock_create, mock_create_education, client):
    http_client, _ = client
    mock_extract.return_value = ProfileExtractionOutput(
        personal_info=PersonalInfoExtract(full_name="Jordan Diaz"),
        education=[EducationIn(school="State University")],
    )
    mock_create.return_value = SimpleNamespace(id=uuid.uuid4())
    mock_get.side_effect = [profile_service.ProfileNotFound(), FAKE_PROFILE_OUT]

    response = _upload(http_client)

    assert response.status_code == 200
    assert response.json()["full_name"] == "Jordan Diaz"
    mock_create.assert_awaited_once()
    mock_create_education.assert_awaited_once()


def test_import_resume_rejects_oversized_file(client):
    http_client, _ = client
    oversized = b"%PDF-1.4 " + b"0" * MAX_UPLOAD_SIZE_BYTES

    response = _upload(http_client, content=oversized)

    assert response.status_code == 413


def test_import_resume_rejects_non_pdf_file(client):
    http_client, _ = client

    response = _upload(http_client, filename="resume.docx", content=b"hello", content_type="application/pdf")

    assert response.status_code == 415


def test_import_resume_rejects_wrong_content_type(client):
    http_client, _ = client

    response = _upload(http_client, content_type="text/plain")

    assert response.status_code == 415


@patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock)
def test_import_resume_corrupted_pdf_returns_422(mock_get, client):
    http_client, _ = client
    mock_get.side_effect = profile_service.ProfileNotFound()

    response = _upload(http_client, content=b"not a real pdf")

    assert response.status_code == 422


@patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock)
def test_import_resume_returns_409_when_profile_already_exists(mock_get, client):
    http_client, _ = client
    mock_get.return_value = FAKE_PROFILE_OUT

    response = _upload(http_client)

    assert response.status_code == 409


@patch("app.services.profile_import_service.education_repo.create_many", new_callable=AsyncMock)
@patch("app.services.profile_import_service.education_repo.delete_many", new_callable=AsyncMock)
@patch("app.services.profile_import_service.profile_service.update_profile", new_callable=AsyncMock)
@patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock)
@patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock)
def test_import_resume_replace_existing_overwrites_profile(
    mock_extract, mock_get, mock_update, mock_delete_education, mock_create_education, client
):
    http_client, _ = client
    existing = FakeExistingProfile()
    mock_extract.return_value = ProfileExtractionOutput(
        personal_info=PersonalInfoExtract(full_name="Jordan Diaz"),
        education=[EducationIn(school="State University")],
    )
    mock_get.side_effect = [existing, FAKE_PROFILE_OUT]

    response = _upload(http_client, replace_existing=True)

    assert response.status_code == 200
    mock_update.assert_awaited_once()
    mock_delete_education.assert_awaited_once_with(
        mock_update.call_args.args[0], [existing.education[0].id], commit=False
    )
    mock_create_education.assert_awaited_once()


@patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock)
@patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock)
def test_import_resume_returns_503_on_ai_provider_error(mock_extract, mock_get, client):
    http_client, _ = client
    mock_extract.side_effect = ai_client.AIProviderError("connection reset")
    mock_get.side_effect = profile_service.ProfileNotFound()

    response = _upload(http_client)

    assert response.status_code == 503


@patch("app.services.profile_import_service.import_resume", new_callable=AsyncMock)
def test_import_resume_rate_limited_after_ten_requests_per_minute(mock_import, client):
    http_client, _ = client
    mock_import.return_value = FAKE_PROFILE_OUT

    responses = [_upload(http_client) for _ in range(11)]

    assert [r.status_code for r in responses[:10]] == [200] * 10
    assert responses[10].status_code == 429
