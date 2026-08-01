import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.projects import Project


async def list_by_profile(db: AsyncSession, profile_id: uuid.UUID) -> list[Project]:
    result = await db.execute(select(Project).where(Project.profile_id == profile_id))
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, profile_id: uuid.UUID, **fields) -> Project:
    item = Project(profile_id=profile_id, **fields)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update(db: AsyncSession, item: Project, **fields) -> Project:
    for key, value in fields.items():
        setattr(item, key, value)
    await db.commit()
    await db.refresh(item)
    return item


async def delete(db: AsyncSession, item: Project) -> None:
    await db.delete(item)
    await db.commit()
