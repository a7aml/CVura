from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.security import limiter, user_id_key
from app.models.user import User
from app.schemas.profile import FullProfileOut, ProfileCreate, ProfileOut, ProfileUpdate
from app.services import profile_import_service, profile_service

router = APIRouter(prefix="/profile", tags=["profile"])

NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


@router.get("", response_model=FullProfileOut)
async def get_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        return await profile_service.get_full_profile(db, user.id)
    except profile_service.ProfileNotFound:
        raise NOT_FOUND


@router.post("", response_model=ProfileOut)
async def create_profile(
    body: ProfileCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await profile_service.create_profile(db, user.id, body)
    except profile_service.ProfileAlreadyExists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profile already exists")


@router.patch("", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    try:
        return await profile_service.update_profile(db, user.id, body)
    except profile_service.ProfileNotFound:
        raise NOT_FOUND


@router.post("/import-resume", response_model=FullProfileOut)
@limiter.limit("10/minute", key_func=user_id_key)
async def import_resume(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    try:
        return await profile_import_service.import_resume(
            db, user.id, file.filename or "", file.content_type, file_bytes
        )
    except profile_import_service.InvalidFileType as e:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(e))
    except profile_import_service.FileTooLarge as e:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, str(e))
    except profile_import_service.ProfileAlreadyExists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Profile already exists")
    except (profile_import_service.PDFExtractionError, profile_import_service.EmptyExtraction) as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except profile_import_service.ExtractionFailed as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except profile_import_service.AIServiceUnavailable as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
