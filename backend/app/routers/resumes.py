import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import limiter, user_id_key
from app.models.user import User
from app.schemas.resume import ResumeTailorResponse
from app.services import job_analysis_service as jobs_service
from app.services import resume_tailor_service

router = APIRouter(prefix="/jobs", tags=["resumes"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


@router.post("/{job_id}/tailor", response_model=ResumeTailorResponse)
@limiter.limit("10/minute", key_func=user_id_key)
async def tailor_resume(
    request: Request,
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tailored, resume = await resume_tailor_service.tailor_resume(db, user.id, job_id)
    except jobs_service.JobNotFound:
        raise NOT_FOUND
    except resume_tailor_service.ProfileNotFound:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    except resume_tailor_service.JobNotAnalyzed as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Job must be analyzed before tailoring") from e
    except resume_tailor_service.TailorInputTooLarge as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except resume_tailor_service.ResumeTailorError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except resume_tailor_service.AIServiceUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))

    return ResumeTailorResponse(**tailored.model_dump(), resume_id=resume.id, version=resume.version)
