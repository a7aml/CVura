import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


async def get_by_id(db: AsyncSession, job_id: uuid.UUID) -> Job | None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def list_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Job]:
    stmt = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_job(db: AsyncSession, user_id: uuid.UUID, **fields) -> Job:
    job = Job(user_id=user_id, **fields)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_analyzed_by_hash(db: AsyncSession, jd_hash: str) -> Job | None:
    stmt = (
        select(Job)
        .where(Job.jd_hash == jd_hash, Job.parsed_json.isnot(None))
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def set_analysis(db: AsyncSession, job: Job, parsed_json: dict, jd_hash: str) -> Job:
    job.parsed_json = parsed_json
    job.jd_hash = jd_hash
    await db.commit()
    await db.refresh(job)
    return job
