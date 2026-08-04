"""Onboarding fast-path: extract a Master Career Profile directly from an
uploaded PDF resume via AI, bypassing the manual wizard. Reuses the same
profile create/section services the wizard uses — this module only adds PDF
text extraction and the AI extraction call on top."""

import io
import uuid

import pypdf

from app.ai import client as ai_client
from app.schemas.profile import ProfileCreate
from app.schemas.profile_import import MAX_UPLOAD_SIZE_BYTES, ProfileExtractionOutput
from app.services import profile_sections_service as sections
from app.services import profile_service

_ALLOWED_CONTENT_TYPE = "application/pdf"
# Below this, treat the PDF as unreadable (scanned image with no text layer,
# corrupted file, etc.) rather than risk saving a near-empty profile.
_MIN_EXTRACTED_TEXT_LENGTH = 50

# Maps each extracted section to the profile_sections_service function name
# that saves it. Looked up by name (not by direct function reference) so the
# dispatch always goes through the current `sections` module attribute.
_SECTION_SAVER_NAMES = {
    "education": "add_education",
    "experiences": "add_experience",
    "projects": "add_project",
    "skills": "add_skill",
    "certifications": "add_certification",
    "languages": "add_language",
    "awards": "add_award",
}


class InvalidFileType(Exception):
    pass


class FileTooLarge(Exception):
    pass


class PDFExtractionError(Exception):
    pass


class ExtractionFailed(Exception):
    pass


class EmptyExtraction(Exception):
    pass


class AIServiceUnavailable(Exception):
    pass


class ProfileAlreadyExists(Exception):
    pass


async def import_resume(
    db, user_id: uuid.UUID, filename: str, content_type: str | None, file_bytes: bytes
):
    """Validate -> extract PDF text -> AI extraction -> save. Nothing is
    written to the DB until the extracted result has passed validation, so a
    failure at any earlier step leaves no partial profile behind."""
    _validate_upload(filename, content_type, file_bytes)
    if await _has_profile(db, user_id):
        raise ProfileAlreadyExists()

    resume_text = _extract_text(file_bytes)

    try:
        extracted = await _extract_with_retry(resume_text)
    except ai_client.ResumeTextTooLong as exc:
        raise ExtractionFailed(str(exc)) from exc

    if not extracted.personal_info.full_name:
        raise EmptyExtraction("could not extract a name from the resume")

    await profile_service.create_profile(db, user_id, _to_profile_create(extracted))
    await _save_sections(db, user_id, extracted)
    return await profile_service.get_full_profile(db, user_id)


def _validate_upload(filename: str, content_type: str | None, file_bytes: bytes) -> None:
    if not filename.lower().endswith(".pdf") or content_type != _ALLOWED_CONTENT_TYPE:
        raise InvalidFileType(f"'{filename}' is not a PDF file")
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLarge(f"file is {len(file_bytes)} bytes, exceeding the {MAX_UPLOAD_SIZE_BYTES}-byte limit")


async def _has_profile(db, user_id: uuid.UUID) -> bool:
    try:
        await profile_service.get_full_profile(db, user_id)
    except profile_service.ProfileNotFound:
        return False
    return True


def _extract_text(file_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise PDFExtractionError("could not read the uploaded PDF") from exc

    text = text.strip()
    if len(text) < _MIN_EXTRACTED_TEXT_LENGTH:
        raise PDFExtractionError("the PDF contains no extractable text")
    return text


async def _extract_with_retry(resume_text: str) -> ProfileExtractionOutput:
    for attempt in range(2):
        try:
            return await ai_client.extract_profile_from_resume(resume_text)
        except ai_client.AIResponseInvalid:
            if attempt == 1:
                raise ExtractionFailed("AI resume extraction failed validation twice") from None
        except ai_client.AIProviderError as exc:
            if attempt == 1:
                raise AIServiceUnavailable("AI provider is temporarily unavailable") from exc


def _to_profile_create(extracted: ProfileExtractionOutput) -> ProfileCreate:
    return ProfileCreate(**extracted.personal_info.model_dump())


async def _save_sections(db, user_id: uuid.UUID, extracted: ProfileExtractionOutput) -> None:
    for field, saver_name in _SECTION_SAVER_NAMES.items():
        saver = getattr(sections, saver_name)
        for item in getattr(extracted, field):
            await saver(db, user_id, item.model_dump())
