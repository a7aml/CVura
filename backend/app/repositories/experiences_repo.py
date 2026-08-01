import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experiences import Experience


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Experience]:
    result = await db.execute(select(Experience).where(Experience.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, experience_id: uuid.UUID) -> Experience | None:
    result = await db.execute(select(Experience).where(Experience.id == experience_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Experience:
    item = Experience(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Experience, **fields) -> Experience:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Experience) -> None:
    await db.delete(item)
    await db.commit()
