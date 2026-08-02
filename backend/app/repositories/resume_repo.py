import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


async def _next_version(db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> int:
    stmt = select(func.max(Resume.version)).where(Resume.user_id == user_id, Resume.job_id == job_id)
    result = await db.execute(stmt)
    current_max = result.scalar()
    return (current_max or 0) + 1


async def create_resume(
    db: AsyncSession,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
    content_json: dict,
    match_explanation: str | None = None,
) -> Resume:
    """Always inserts a new row — resumes are versioned, never overwritten."""
    version = await _next_version(db, user_id, job_id)
    resume = Resume(
        user_id=user_id,
        job_id=job_id,
        version=version,
        content_json=content_json,
        match_explanation=match_explanation,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


async def update_pdf_url(db: AsyncSession, resume_id: uuid.UUID, user_id: uuid.UUID, url: str | None) -> Resume | None:
    """Ownership-checked: only updates a resume row owned by user_id. Returns
    None (no-op) if the resume doesn't exist or belongs to someone else."""
    stmt = select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    if resume is None:
        return None
    resume.pdf_url = url
    await db.commit()
    await db.refresh(resume)
    return resume


async def get_resumes_by_job(db: AsyncSession, job_id: uuid.UUID, user_id: uuid.UUID) -> list[Resume]:
    """Filters by user_id as well as job_id so a caller can never fetch
    another user's resumes for a job_id they don't own (IDOR)."""
    stmt = (
        select(Resume)
        .where(Resume.job_id == job_id, Resume.user_id == user_id)
        .order_by(Resume.version.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
