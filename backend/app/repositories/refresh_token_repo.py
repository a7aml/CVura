import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.refresh_token import RefreshToken


async def create(
    db: AsyncSession, user_id: uuid.UUID, token_hash: str, expires_at: datetime
) -> RefreshToken:
    token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def get_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    return result.scalar_one_or_none()


async def mark_used(db: AsyncSession, token: RefreshToken) -> None:
    token.used_at = func.now()
    await db.commit()
    await db.refresh(token)


async def consume(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    """Atomically mark a refresh token used, iff it is still unused and unrevoked.

    The WHERE clause and the write happen in a single statement, so two
    concurrent callers presenting the same single-use token can never both
    succeed: whichever commits first wins, and the loser's UPDATE matches
    zero rows. Callers must treat a None return as a reuse signal, not merely
    "not found".
    """
    result = await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.used_at.is_(None),
            RefreshToken.revoked_at.is_(None),
        )
        .values(used_at=func.now())
        .returning(RefreshToken)
    )
    await db.commit()
    return result.scalar_one_or_none()


async def revoke(db: AsyncSession, token: RefreshToken) -> None:
    token.revoked_at = func.now()
    await db.commit()
    await db.refresh(token)


async def revoke_all_for_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    await db.commit()
