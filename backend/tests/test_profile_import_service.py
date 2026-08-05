import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import typst
from sqlalchemy import text

from app.ai import client as ai_client
from app.repositories import education_repo, profile_repo, user_repo
from app.schemas.profile import EducationIn, ExperienceIn
from app.schemas.profile_import import MAX_UPLOAD_SIZE_BYTES, PersonalInfoExtract, ProfileExtractionOutput
from app.services import profile_import_service, profile_service


def _real_pdf_bytes(text: str) -> bytes:
    """Compiles a real single-page PDF containing `text` via Typst (already a
    dependency for resume PDF generation) so extraction is exercised against
    an actual PDF rather than a hand-rolled fake."""
    with tempfile.TemporaryDirectory() as tmpdir:
        typ_path = Path(tmpdir) / "doc.typ"
        typ_path.write_text(text, encoding="utf-8")
        return typst.compile(str(typ_path))


VALID_PDF = _real_pdf_bytes("Jordan Diaz\nSoftware Engineer with 5 years of experience at Acme Corp.")
BLANK_PDF = _real_pdf_bytes("")

SAMPLE_EXTRACTION = ProfileExtractionOutput(
    personal_info=PersonalInfoExtract(full_name="Jordan Diaz", summary="Backend engineer."),
    education=[EducationIn(school="State University", degree="BSc Computer Science")],
    experiences=[ExperienceIn(title="Software Engineer", company="Acme Corp", bullets=["Built APIs"])],
)

EMPTY_EXTRACTION = ProfileExtractionOutput(personal_info=PersonalInfoExtract())

_NO_EXISTING_PROFILE = profile_service.ProfileNotFound()


class _FakeProfile:
    def __init__(self):
        self.id = uuid.uuid4()


async def test_import_resume_happy_path_saves_extracted_sections():
    # A mock "db" (not None) because _persist_extracted_profile now calls
    # db.commit()/db.rollback() itself around the save, and the asserts below
    # check it's committed exactly once -- not once per section like before.
    db = AsyncMock(name="db")
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
        patch("app.services.profile_import_service.profile_service.create_profile", new_callable=AsyncMock) as mock_create,
        patch("app.services.profile_import_service.education_repo.create_many", new_callable=AsyncMock) as mock_create_education,
        patch("app.services.profile_import_service.experiences_repo.create_many", new_callable=AsyncMock) as mock_create_experience,
        patch("app.services.profile_import_service.projects_repo.create_many", new_callable=AsyncMock) as mock_create_project,
    ):
        mock_extract.return_value = SAMPLE_EXTRACTION
        new_profile = _FakeProfile()
        mock_create.return_value = new_profile
        mock_get.side_effect = [_NO_EXISTING_PROFILE, "final-profile"]

        result = await profile_import_service.import_resume(
            db, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF
        )

    assert result == "final-profile"
    mock_create.assert_awaited_once()
    saved_profile_create = mock_create.call_args.args[2]
    assert saved_profile_create.full_name == "Jordan Diaz"
    mock_create_education.assert_awaited_once_with(
        db,
        new_profile.id,
        [{"school": "State University", "degree": "BSc Computer Science", "field": None, "start_date": None, "end_date": None}],
        commit=False,
    )
    mock_create_experience.assert_awaited_once()
    mock_create_project.assert_not_awaited()
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_import_resume_does_not_invent_data_for_missing_sections():
    """Sections absent from the AI output must never be saved as invented
    placeholder entries."""
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
        patch("app.services.profile_import_service.profile_service.create_profile", new_callable=AsyncMock) as mock_create,
        patch("app.services.profile_import_service.education_repo.create_many", new_callable=AsyncMock) as mock_education,
        patch("app.services.profile_import_service.experiences_repo.create_many", new_callable=AsyncMock) as mock_experience,
        patch("app.services.profile_import_service.projects_repo.create_many", new_callable=AsyncMock) as mock_project,
        patch("app.services.profile_import_service.skills_repo.create_many", new_callable=AsyncMock) as mock_skill,
        patch("app.services.profile_import_service.certifications_repo.create_many", new_callable=AsyncMock) as mock_cert,
        patch("app.services.profile_import_service.languages_repo.create_many", new_callable=AsyncMock) as mock_language,
        patch("app.services.profile_import_service.awards_repo.create_many", new_callable=AsyncMock) as mock_award,
    ):
        mock_extract.return_value = ProfileExtractionOutput(personal_info=PersonalInfoExtract(full_name="Jordan Diaz"))
        mock_create.return_value = _FakeProfile()
        mock_get.side_effect = [_NO_EXISTING_PROFILE, "final-profile"]

        db = AsyncMock(name="db")
        await profile_import_service.import_resume(db, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF)

    for saver_mock in (mock_education, mock_experience, mock_project, mock_skill, mock_cert, mock_language, mock_award):
        saver_mock.assert_not_awaited()
    db.commit.assert_awaited_once()


async def test_import_resume_rejects_non_pdf_extension():
    with pytest.raises(profile_import_service.InvalidFileType):
        await profile_import_service.import_resume(None, uuid.uuid4(), "resume.docx", "application/pdf", VALID_PDF)


async def test_import_resume_rejects_wrong_content_type():
    with pytest.raises(profile_import_service.InvalidFileType):
        await profile_import_service.import_resume(None, uuid.uuid4(), "resume.pdf", "text/plain", VALID_PDF)


async def test_import_resume_rejects_oversized_file():
    oversized = b"%PDF-1.4 " + b"0" * MAX_UPLOAD_SIZE_BYTES

    with pytest.raises(profile_import_service.FileTooLarge):
        await profile_import_service.import_resume(None, uuid.uuid4(), "resume.pdf", "application/pdf", oversized)


async def test_import_resume_corrupted_pdf_raises_extraction_error():
    with patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = _NO_EXISTING_PROFILE

        with pytest.raises(profile_import_service.PDFExtractionError):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", b"not a real pdf"
            )


async def test_import_resume_blank_pdf_raises_extraction_error():
    with patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = _NO_EXISTING_PROFILE

        with pytest.raises(profile_import_service.PDFExtractionError):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", BLANK_PDF
            )


async def test_import_resume_existing_profile_raises_without_calling_ai():
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = "existing-profile"

        with pytest.raises(profile_import_service.ProfileAlreadyExists):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF
            )

    mock_extract.assert_not_awaited()


async def test_import_resume_empty_ai_extraction_raises_without_saving():
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
        patch("app.services.profile_import_service.profile_service.create_profile", new_callable=AsyncMock) as mock_create,
    ):
        mock_extract.return_value = EMPTY_EXTRACTION
        mock_get.side_effect = _NO_EXISTING_PROFILE

        with pytest.raises(profile_import_service.EmptyExtraction):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF
            )

    mock_create.assert_not_awaited()


async def test_import_resume_ai_validation_failure_retries_then_raises():
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
    ):
        mock_extract.side_effect = ai_client.AIResponseInvalid("bad output")
        mock_get.side_effect = _NO_EXISTING_PROFILE

        with pytest.raises(profile_import_service.ExtractionFailed):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF
            )

    assert mock_extract.await_count == 2


async def test_import_resume_ai_provider_error_retries_then_raises_unavailable():
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
    ):
        mock_extract.side_effect = ai_client.AIProviderError("connection reset")
        mock_get.side_effect = _NO_EXISTING_PROFILE

        with pytest.raises(profile_import_service.AIServiceUnavailable):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF
            )

    assert mock_extract.await_count == 2


class _FakeItem:
    def __init__(self):
        self.id = uuid.uuid4()


class _FakeExistingProfile:
    """Stands in for the SQLAlchemy Profile object returned by
    get_full_profile: has one stale item per section, so a replace's
    clear-then-save behavior can be asserted."""

    def __init__(self):
        self.id = uuid.uuid4()
        self.education = [_FakeItem()]
        self.experiences = [_FakeItem()]
        self.projects = []
        self.skills = []
        self.certifications = []
        self.languages = []
        self.awards = []


async def test_import_resume_replace_existing_updates_and_replaces_sections():
    existing = _FakeExistingProfile()
    db = AsyncMock(name="db")
    with (
        patch("app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock) as mock_extract,
        patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get,
        patch("app.services.profile_import_service.profile_service.update_profile", new_callable=AsyncMock) as mock_update,
        patch("app.services.profile_import_service.profile_service.create_profile", new_callable=AsyncMock) as mock_create,
        patch("app.services.profile_import_service.education_repo.delete_many", new_callable=AsyncMock) as mock_delete_education,
        patch("app.services.profile_import_service.experiences_repo.delete_many", new_callable=AsyncMock) as mock_delete_experience,
        patch("app.services.profile_import_service.education_repo.create_many", new_callable=AsyncMock) as mock_create_education,
        patch("app.services.profile_import_service.experiences_repo.create_many", new_callable=AsyncMock) as mock_create_experience,
    ):
        mock_extract.return_value = SAMPLE_EXTRACTION
        mock_get.side_effect = [existing, "final-profile"]

        result = await profile_import_service.import_resume(
            db, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF, replace_existing=True
        )

    assert result == "final-profile"
    mock_create.assert_not_awaited()
    mock_update.assert_awaited_once()
    saved_update = mock_update.call_args.args[2]
    assert saved_update.full_name == "Jordan Diaz"
    mock_delete_education.assert_awaited_once_with(db, [existing.education[0].id], commit=False)
    mock_delete_experience.assert_awaited_once_with(db, [existing.experiences[0].id], commit=False)
    mock_create_education.assert_awaited_once_with(
        db, existing.id, [item.model_dump() for item in SAMPLE_EXTRACTION.education], commit=False
    )
    mock_create_experience.assert_awaited_once()
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_import_resume_replace_existing_false_still_blocks_on_existing_profile():
    with patch("app.services.profile_import_service.profile_service.get_full_profile", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _FakeExistingProfile()

        with pytest.raises(profile_import_service.ProfileAlreadyExists):
            await profile_import_service.import_resume(
                None, uuid.uuid4(), "resume.pdf", "application/pdf", VALID_PDF, replace_existing=False
            )


async def _cleanup_real_db(db_session, user_id):
    for table in ("education", "experiences", "profiles", "users"):
        where = "profile_id in (select id from profiles where user_id = :uid)" if table in (
            "education",
            "experiences",
        ) else ("user_id = :uid" if table == "profiles" else "id = :uid")
        await db_session.execute(text(f"delete from {table} where {where}"), {"uid": str(user_id)})
    await db_session.commit()


async def test_import_resume_replace_failure_partway_rolls_back_everything(db_session):
    """Integration-style: real DB, real repos for education, only the
    experiences save is forced to fail. Proves a mid-way failure leaves zero
    trace -- not the old education row deleted, not the new one inserted --
    rather than a real DB commit per section like before this fix."""
    user = await user_repo.create_local_user(db_session, f"rollback-test-{uuid.uuid4()}@example.com", "hash")
    user_id = user.id  # captured before expire_all() below, which invalidates lazy sync attribute access
    try:
        profile = await profile_repo.create_profile(db_session, user.id, full_name="Old Name")
        await education_repo.create(db_session, profile.id, school="Old School")

        extracted = ProfileExtractionOutput(
            personal_info=PersonalInfoExtract(full_name="New Name"),
            education=[EducationIn(school="New School")],
            experiences=[ExperienceIn(title="New Title", company="New Co")],
        )

        with (
            patch(
                "app.services.profile_import_service.ai_client.extract_profile_from_resume", new_callable=AsyncMock
            ) as mock_extract,
            patch(
                "app.services.profile_import_service.experiences_repo.create_many",
                new_callable=AsyncMock,
                side_effect=RuntimeError("simulated failure mid-save"),
            ),
        ):
            mock_extract.return_value = extracted
            with pytest.raises(RuntimeError, match="simulated failure mid-save"):
                await profile_import_service.import_resume(
                    db_session, user_id, "resume.pdf", "application/pdf", VALID_PDF, replace_existing=True
                )

        db_session.expire_all()
        reloaded = await profile_repo.get_by_user_id(db_session, user_id)
        assert reloaded.full_name == "Old Name"
        assert len(reloaded.education) == 1
        assert reloaded.education[0].school == "Old School"
    finally:
        await _cleanup_real_db(db_session, user_id)
