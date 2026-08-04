"""Fast-path resume import: extract a Master Career Profile directly from an
uploaded PDF resume via AI, bypassing the manual wizard. Used both for
onboarding (no profile yet) and for replacing an existing profile once the
caller has confirmed the overwrite.

Section writes go through the repositories directly (create_many/
delete_many) rather than profile_sections_service's one-item-at-a-time
add/delete: a real resume can have dozens of section entries, and each of
those going through a separate DB round-trip (plus that service's per-call
ownership re-check) made a single import take minutes. Batching keeps the
same repository layer, just fewer, bigger round-trips."""

import io
import uuid

import pypdf

from app.ai import client as ai_client
from app.repositories import (
    awards_repo,
    certifications_repo,
    education_repo,
    experiences_repo,
    languages_repo,
    projects_repo,
    skills_repo,
)
from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.schemas.profile_import import MAX_UPLOAD_SIZE_BYTES, ProfileExtractionOutput
from app.services import profile_service

_ALLOWED_CONTENT_TYPE = "application/pdf"
# Below this, treat the PDF as unreadable (scanned image with no text layer,
# corrupted file, etc.) rather than risk saving a near-empty profile.
_MIN_EXTRACTED_TEXT_LENGTH = 50

# Maps each extracted section to the repository that owns it.
_SECTION_REPOS = {
    "education": education_repo,
    "experiences": experiences_repo,
    "projects": projects_repo,
    "skills": skills_repo,
    "certifications": certifications_repo,
    "languages": languages_repo,
    "awards": awards_repo,
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
    db,
    user_id: uuid.UUID,
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
    replace_existing: bool = False,
):
    """Validate -> extract PDF text -> AI extraction -> save. Nothing is
    written to the DB until the extracted result has passed validation, so a
    failure at any earlier step leaves no partial profile behind.

    If the user already has a profile, this refuses to touch it unless
    `replace_existing` is set — the caller must get explicit confirmation
    first, since a successful import wholly replaces the existing profile."""
    _validate_upload(filename, content_type, file_bytes)
    existing_profile = await _get_existing_profile(db, user_id)
    if existing_profile is not None and not replace_existing:
        raise ProfileAlreadyExists()

    resume_text = _extract_text(file_bytes)

    try:
        extracted = await _extract_with_retry(resume_text)
    except ai_client.ResumeTextTooLong as exc:
        raise ExtractionFailed(str(exc)) from exc

    if not extracted.personal_info.full_name:
        raise EmptyExtraction("could not extract a name from the resume")

    if existing_profile is not None:
        await profile_service.update_profile(db, user_id, _to_profile_update(extracted))
        await _clear_sections(db, existing_profile)
        profile_id = existing_profile.id
    else:
        new_profile = await profile_service.create_profile(db, user_id, _to_profile_create(extracted))
        profile_id = new_profile.id

    await _save_sections(db, profile_id, extracted)
    return await profile_service.get_full_profile(db, user_id)


def _validate_upload(filename: str, content_type: str | None, file_bytes: bytes) -> None:
    if not filename.lower().endswith(".pdf") or content_type != _ALLOWED_CONTENT_TYPE:
        raise InvalidFileType(f"'{filename}' is not a PDF file")
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        raise FileTooLarge(f"file is {len(file_bytes)} bytes, exceeding the {MAX_UPLOAD_SIZE_BYTES}-byte limit")


async def _get_existing_profile(db, user_id: uuid.UUID):
    try:
        return await profile_service.get_full_profile(db, user_id)
    except profile_service.ProfileNotFound:
        return None


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


def _to_profile_update(extracted: ProfileExtractionOutput) -> ProfileUpdate:
    # Every field is passed explicitly (not just the ones the resume filled
    # in) so a replace wipes fields the new resume doesn't mention, rather
    # than leaving stale data from the old profile mixed in.
    return ProfileUpdate(**extracted.personal_info.model_dump())


async def _save_sections(db, profile_id: uuid.UUID, extracted: ProfileExtractionOutput) -> None:
    for field, repo in _SECTION_REPOS.items():
        items = [item.model_dump() for item in getattr(extracted, field)]
        if items:
            await repo.create_many(db, profile_id, items)


async def _clear_sections(db, existing_profile) -> None:
    for field, repo in _SECTION_REPOS.items():
        ids = [item.id for item in getattr(existing_profile, field)]
        if ids:
            await repo.delete_many(db, ids)
