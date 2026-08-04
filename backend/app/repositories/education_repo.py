import uuid

from sqlalchemy import delete as sql_delete
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


async def create_many(db: AsyncSession, profile_id: uuid.UUID, items: list[dict]) -> list[Education]:
    """Bulk insert in a single commit — used by resume import, where saving
    each section item as its own round-trip is too slow for a real resume."""
    rows = [Education(profile_id=profile_id, **fields) for fields in items]
    db.add_all(rows)
    await db.commit()
    return rows


async def delete_many(db: AsyncSession, ids: list[uuid.UUID]) -> None:
    if not ids:
        return
    await db.execute(sql_delete(Education).where(Education.id.in_(ids)))
    await db.commit()
