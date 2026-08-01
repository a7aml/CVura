import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skills import Skill


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Skill]:
    result = await db.execute(select(Skill).where(Skill.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, skill_id: uuid.UUID) -> Skill | None:
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Skill:
    item = Skill(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Skill, **fields) -> Skill:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Skill) -> None:
    await db.delete(item)
    await db.commit()
