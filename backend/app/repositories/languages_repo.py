import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.languages import Language


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Language]:
    result = await db.execute(select(Language).where(Language.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, language_id: uuid.UUID) -> Language | None:
    result = await db.execute(select(Language).where(Language.id == language_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Language:
    item = Language(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Language, **fields) -> Language:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Language) -> None:
    await db.delete(item)
    await db.commit()
