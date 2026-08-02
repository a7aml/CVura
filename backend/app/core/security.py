import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

# key_style="endpoint": slowapi defaults to keying by the literal URL, which
# would let a caller bypass an AI-endpoint's rate limit just by rotating the
# {job_id} path param. Keying by (key_func result, view function) instead
# makes the limit apply per-user across all of that user's requests to the
# endpoint, which is what "rate limit all AI-calling endpoints" requires.
limiter = Limiter(key_func=get_remote_address, key_style="endpoint")

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _create_token(user_id: uuid.UUID, token_type: Literal["access", "refresh"], expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> dict:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected a {expected_type} token")
    return payload


def user_id_key(request: Request) -> str:
    """Rate-limit key for authenticated, AI-calling endpoints — keys by the
    authenticated user (decoded from the access token cookie) rather than the
    client IP, so the limit can't be bypassed by rotating IPs on one account.
    Falls back to IP if the request has no valid access token (the route's own
    auth dependency rejects those requests before they do any real work)."""
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = decode_token(token, expected_type="access")
        except jwt.InvalidTokenError:
            pass
        else:
            return f"user:{payload['sub']}"
    return get_remote_address(request)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_google_id_token(token: str) -> dict:
    return google_id_token.verify_oauth2_token(
        token, google_requests.Request(), audience=settings.google_client_id
    )
