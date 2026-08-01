import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_google_id_token,
    verify_password,
)
from app.models.user import User
from app.repositories import refresh_token_repo, user_repo


class EmailAlreadyExists(Exception):
    pass


class InvalidCredentials(Exception):
    pass


class GoogleAccountConflict(Exception):
    pass


class InvalidRefreshToken(Exception):
    pass


async def issue_tokens(db, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await refresh_token_repo.create(db, user.id, hash_token(refresh_token), expires_at)
    return access_token, refresh_token


async def signup_local(db, email: str, password: str) -> tuple[User, str, str]:
    if await user_repo.get_by_email(db, email) is not None:
        raise EmailAlreadyExists()
    user = await user_repo.create_local_user(db, email, hash_password(password))
    access_token, refresh_token = await issue_tokens(db, user)
    return user, access_token, refresh_token


async def login_local(db, email: str, password: str) -> tuple[User, str, str]:
    user = await user_repo.get_by_email(db, email)
    if user is None or user.password_hash is None or not verify_password(password, user.password_hash):
        raise InvalidCredentials()
    access_token, refresh_token = await issue_tokens(db, user)
    return user, access_token, refresh_token


async def login_google(db, id_token: str) -> tuple[User, str, str]:
    claims = verify_google_id_token(id_token)
    google_sub = claims["sub"]
    email = claims["email"]

    user = await user_repo.get_by_google_sub(db, google_sub)
    if user is None:
        if await user_repo.get_by_email(db, email) is not None:
            raise GoogleAccountConflict()
        user = await user_repo.create_google_user(db, email, google_sub)

    access_token, refresh_token = await issue_tokens(db, user)
    return user, access_token, refresh_token


async def refresh_access_token(db, refresh_token: str) -> tuple[User, str, str]:
    try:
        payload = decode_token(refresh_token, expected_type="refresh")
    except jwt.InvalidTokenError:
        raise InvalidRefreshToken()

    stored = await refresh_token_repo.get_by_hash(db, hash_token(refresh_token))
    if stored is None or stored.revoked_at is not None:
        raise InvalidRefreshToken()

    if stored.used_at is not None:
        # Reuse of an already-rotated refresh token — likely theft. Revoke the whole family.
        await refresh_token_repo.revoke_all_for_user(db, stored.user_id)
        raise InvalidRefreshToken()

    if stored.expires_at < datetime.now(timezone.utc):
        raise InvalidRefreshToken()

    await refresh_token_repo.mark_used(db, stored)

    user = await user_repo.get_by_id(db, uuid.UUID(payload["sub"]))
    if user is None:
        raise InvalidRefreshToken()

    access_token, new_refresh_token = await issue_tokens(db, user)
    return user, access_token, new_refresh_token


async def logout(db, refresh_token: str) -> None:
    stored = await refresh_token_repo.get_by_hash(db, hash_token(refresh_token))
    if stored is not None:
        await refresh_token_repo.revoke(db, stored)
