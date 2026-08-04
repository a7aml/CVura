"""CRUD for the repeatable Master Career Profile sections (education,
experiences, projects, skills, certifications, languages, awards). Split out
of routers/profile.py to keep that file under the file-size limit."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import (
    AwardIn,
    AwardOut,
    CertificationIn,
    CertificationOut,
    EducationIn,
    EducationOut,
    ExperienceIn,
    ExperienceOut,
    LanguageIn,
    LanguageOut,
    ProjectIn,
    ProjectOut,
    SkillIn,
    SkillOut,
)
from app.services import profile_sections_service as sections

router = APIRouter(prefix="/profile", tags=["profile"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


# --- education ---


@router.post("/education", response_model=EducationOut)
async def add_education(
    body: EducationIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_education(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/education/{item_id}", response_model=EducationOut)
async def update_education(
    item_id: uuid.UUID,
    body: EducationIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_education(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/education/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_education(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- experiences ---


@router.post("/experiences", response_model=ExperienceOut)
async def add_experience(
    body: ExperienceIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_experience(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/experiences/{item_id}", response_model=ExperienceOut)
async def update_experience(
    item_id: uuid.UUID,
    body: ExperienceIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_experience(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/experiences/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_experience(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- projects ---


@router.post("/projects", response_model=ProjectOut)
async def add_project(
    body: ProjectIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_project(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/projects/{item_id}", response_model=ProjectOut)
async def update_project(
    item_id: uuid.UUID,
    body: ProjectIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_project(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/projects/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_project(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- skills ---


@router.post("/skills", response_model=SkillOut)
async def add_skill(
    body: SkillIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_skill(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/skills/{item_id}", response_model=SkillOut)
async def update_skill(
    item_id: uuid.UUID,
    body: SkillIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_skill(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/skills/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_skill(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- certifications ---


@router.post("/certifications", response_model=CertificationOut)
async def add_certification(
    body: CertificationIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_certification(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/certifications/{item_id}", response_model=CertificationOut)
async def update_certification(
    item_id: uuid.UUID,
    body: CertificationIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_certification(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/certifications/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_certification(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- languages ---


@router.post("/languages", response_model=LanguageOut)
async def add_language(
    body: LanguageIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_language(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/languages/{item_id}", response_model=LanguageOut)
async def update_language(
    item_id: uuid.UUID,
    body: LanguageIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_language(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/languages/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_language(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_language(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


# --- awards ---


@router.post("/awards", response_model=AwardOut)
async def add_award(
    body: AwardIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await sections.add_award(db, user.id, body.model_dump())
    except sections.ProfileNotFound:
        raise NOT_FOUND


@router.patch("/awards/{item_id}", response_model=AwardOut)
async def update_award(
    item_id: uuid.UUID,
    body: AwardIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await sections.update_award(db, user.id, item_id, body.model_dump())
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND


@router.delete("/awards/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_award(
    item_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        await sections.delete_award(db, user.id, item_id)
    except (sections.ProfileNotFound, sections.ItemNotFound):
        raise NOT_FOUND
