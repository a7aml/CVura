import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import limiter
from app.models.user import User
from app.schemas.job import JobCreate, JobOut
from app.services import job_analysis_service as jobs_service

router = APIRouter(prefix="/jobs", tags=["jobs"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


@router.post("", response_model=JobOut)
async def create_job(
    body: JobCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    return await jobs_service.create_job(db, user.id, body.model_dump())


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await jobs_service.get_job(db, user.id, job_id)
    except jobs_service.JobNotFound:
        raise NOT_FOUND


@router.get("", response_model=list[JobOut])
async def list_jobs(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await jobs_service.list_jobs(db, user.id)


@router.post("/{job_id}/analyze", response_model=JobOut)
@limiter.limit("10/minute")
async def analyze_job(
    request: Request,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await jobs_service.analyze_job(db, user.id, job_id)
    except jobs_service.JobNotFound:
        raise NOT_FOUND
    except jobs_service.JobAnalysisError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
