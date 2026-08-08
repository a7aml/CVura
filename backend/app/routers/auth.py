from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import limiter
from app.schemas.user import GoogleLoginRequest, LoginRequest, SignupRequest, UserPublic
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE = settings.access_token_expire_minutes * 60
REFRESH_COOKIE_MAX_AGE = settings.refresh_token_expire_days * 86400


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    # SameSite="none" is required (not just "lax"/"strict") because the caller is a
    # chrome-extension:// origin making a cross-site request to the API's own origin.
    response.set_cookie(
        "access_token", access_token, max_age=ACCESS_COOKIE_MAX_AGE,
        httponly=True, secure=True, samesite="none",
    )
    response.set_cookie(
        "refresh_token", refresh_token, max_age=REFRESH_COOKIE_MAX_AGE,
        httponly=True, secure=True, samesite="none",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", httponly=True, secure=True, samesite="none")
    response.delete_cookie("refresh_token", httponly=True, secure=True, samesite="none")


@router.post("/signup", response_model=UserPublic)
@limiter.limit("5/minute")
async def signup(
    request: Request, body: SignupRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        user, access_token, refresh_token = await auth_service.signup_local(db, body.email, body.password)
    except auth_service.EmailAlreadyExists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/login", response_model=UserPublic)
@limiter.limit("5/minute")
async def login(
    request: Request, body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        user, access_token, refresh_token = await auth_service.login_local(db, body.email, body.password)
    except auth_service.InvalidCredentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    _set_auth_cookies(response, access_token, refresh_token)
    return user


@router.post("/google", response_model=UserPublic)
@limiter.limit("5/minute")
async def google_login(
    request: Request, body: GoogleLoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        user, access_token, refresh_token = await auth_service.login_google(db, body.id_token)
    except auth_service.GoogleAccountConflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered with a password")
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid Google token")
    _set_auth_cookies(response, access_token, refresh_token)
    return user


# Higher than login/signup's 5/minute: unlike those, refresh fires on every
# normal app/extension open and can legitimately repeat every few minutes
# across tabs — 30/minute leaves headroom for that while still bounding a
# buggy retry loop or abuse against this DB-writing endpoint.
@router.post("/refresh", response_model=UserPublic)
@limiter.limit("30/minute")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        user, access_token, new_refresh_token = await auth_service.refresh_access_token(db, refresh_token)
    except auth_service.InvalidRefreshToken:
        _clear_auth_cookies(response)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    _set_auth_cookies(response, access_token, new_refresh_token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token is not None:
        await auth_service.logout(db, refresh_token)
    _clear_auth_cookies(response)
