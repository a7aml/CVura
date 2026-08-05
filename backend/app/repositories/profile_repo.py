import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile


def _with_children(stmt):
    return stmt.options(
        selectinload(Profile.education),
        selectinload(Profile.experiences),
        selectinload(Profile.projects),
        selectinload(Profile.skills),
        selectinload(Profile.certifications),
        selectinload(Profile.languages),
        selectinload(Profile.awards),
    )


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Profile | None:
    stmt = _with_children(select(Profile).where(Profile.user_id == user_id))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, profile_id: uuid.UUID) -> Profile | None:
    result = await db.execute(select(Profile).where(Profile.id == profile_id))
    return result.scalar_one_or_none()


async def create_profile(db: AsyncSession, user_id: uuid.UUID, commit: bool = True, **fields) -> Profile:
    profile = Profile(user_id=user_id, **fields)
    db.add(profile)
    await (db.commit() if commit else db.flush())
    await db.refresh(profile)
    return profile


async def update_profile(db: AsyncSession, profile: Profile, commit: bool = True, **fields) -> Profile:
    for key, value in fields.items():
        setattr(profile, key, value)
    await (db.commit() if commit else db.flush())
    await db.refresh(profile)
    return profile
