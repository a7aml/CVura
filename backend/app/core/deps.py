import uuid
from collections.abc import AsyncGenerator

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.repositories import user_repo


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    token = request.cookies.get("access_token")
    if not token:
        raise unauthorized

    try:
        payload = decode_token(token, expected_type="access")
    except jwt.InvalidTokenError:
        raise unauthorized

    user = await user_repo.get_by_id(db, uuid.UUID(payload["sub"]))
    if user is None:
        raise unauthorized
    return user
