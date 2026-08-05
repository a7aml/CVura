import uuid

from sqlalchemy import delete as sql_delete
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


async def create_many(
    db: AsyncSession, profile_id: uuid.UUID, items: list[dict], commit: bool = True
) -> list[Experience]:
    """Bulk insert in a single round-trip — used by resume import, where saving
    each section item as its own round-trip is too slow for a real resume.
    commit=False lets a caller (e.g. a multi-section replace) batch this into
    a single all-or-nothing transaction instead of committing per section."""
    rows = [Experience(profile_id=profile_id, **fields) for fields in items]
    db.add_all(rows)
    await (db.commit() if commit else db.flush())
    return rows


async def delete_many(db: AsyncSession, ids: list[uuid.UUID], commit: bool = True) -> None:
    if not ids:
        return
    await db.execute(sql_delete(Experience).where(Experience.id.in_(ids)))
    await (db.commit() if commit else db.flush())
