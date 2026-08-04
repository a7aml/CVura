import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certifications import Certification


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Certification]:
    result = await db.execute(select(Certification).where(Certification.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, certification_id: uuid.UUID) -> Certification | None:
    result = await db.execute(select(Certification).where(Certification.id == certification_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Certification:
    item = Certification(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Certification, **fields) -> Certification:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Certification) -> None:
    await db.delete(item)
    await db.commit()


async def create_many(db: AsyncSession, profile_id: uuid.UUID, items: list[dict]) -> list[Certification]:
    """Bulk insert in a single commit — used by resume import, where saving
    each section item as its own round-trip is too slow for a real resume."""
    rows = [Certification(profile_id=profile_id, **fields) for fields in items]
    db.add_all(rows)
    await db.commit()
    return rows


async def delete_many(db: AsyncSession, ids: list[uuid.UUID]) -> None:
    if not ids:
        return
    await db.execute(sql_delete(Certification).where(Certification.id.in_(ids)))
    await db.commit()
