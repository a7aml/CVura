import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.education import Education


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Education]:
    result = await db.execute(select(Education).where(Education.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, education_id: uuid.UUID) -> Education | None:
    result = await db.execute(select(Education).where(Education.id == education_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Education:
    item = Education(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Education, **fields) -> Education:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Education) -> None:
    await db.delete(item)
    await db.commit()
