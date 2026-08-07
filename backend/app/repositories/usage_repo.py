import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import Usage


async def get_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Usage | None:
    result = await db.execute(select(Usage).where(Usage.user_id == user_id))
    return result.scalar_one_or_none()


async def get_or_create(db: AsyncSession, user_id: uuid.UUID) -> Usage:
    """No usage row is created at signup, so a brand-new account has none
    until its first quota check — create it lazily with model defaults."""
    usage = await get_by_user_id(db, user_id)
    if usage is not None:
        return usage
    usage = Usage(user_id=user_id)
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return usage


async def increment_resumes_generated(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(Usage)
        .where(Usage.user_id == user_id)
        .values(resumes_generated_count=Usage.resumes_generated_count + 1)
    )
    await db.commit()
