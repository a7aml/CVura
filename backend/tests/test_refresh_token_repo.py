import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.core.db import AsyncSessionLocal
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import refresh_token_repo, user_repo


async def _make_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    return await user_repo.create_local_user(db_session, email, "hash")


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_create_get_mark_used_revoke(db_session):
    user = await _make_user(db_session)
    try:
        token_hash = f"hash-{uuid.uuid4()}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        token = await refresh_token_repo.create(db_session, user.id, token_hash, expires_at)
        assert token.used_at is None
        assert token.revoked_at is None

        fetched = await refresh_token_repo.get_by_hash(db_session, token_hash)
        assert fetched is not None
        assert fetched.id == token.id

        await refresh_token_repo.mark_used(db_session, fetched)
        assert fetched.used_at is not None

        await refresh_token_repo.revoke(db_session, fetched)
        assert fetched.revoked_at is not None
    finally:
        await _cleanup(db_session, user.id)


async def test_consume_concurrent_calls_only_one_wins(db_session):
    # Regression test for the refresh-token rotation race: two requests
    # presenting the same single-use token at the same instant must not both
    # be able to consume it. Uses two independent DB connections (mirroring
    # two separate concurrent /auth/refresh requests, each with its own
    # AsyncSession) racing a real `UPDATE ... WHERE used_at IS NULL` against
    # Postgres, not mocks — a check-then-act version of `consume` would let
    # both succeed here.
    user = await _make_user(db_session)
    try:
        token_hash = f"hash-{uuid.uuid4()}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        await refresh_token_repo.create(db_session, user.id, token_hash, expires_at)

        async with AsyncSessionLocal() as session_a, AsyncSessionLocal() as session_b:
            result_a, result_b = await asyncio.gather(
                refresh_token_repo.consume(session_a, token_hash),
                refresh_token_repo.consume(session_b, token_hash),
            )

        winners = [r for r in (result_a, result_b) if r is not None]
        assert len(winners) == 1

        fetched = await refresh_token_repo.get_by_hash(db_session, token_hash)
        assert fetched.used_at is not None
    finally:
        await _cleanup(db_session, user.id)


async def test_consume_already_used_token_returns_none(db_session):
    user = await _make_user(db_session)
    try:
        token_hash = f"hash-{uuid.uuid4()}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        await refresh_token_repo.create(db_session, user.id, token_hash, expires_at)

        first = await refresh_token_repo.consume(db_session, token_hash)
        assert first is not None

        second = await refresh_token_repo.consume(db_session, token_hash)
        assert second is None
    finally:
        await _cleanup(db_session, user.id)


async def test_revoke_all_for_user(db_session):
    user = await _make_user(db_session)
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        hash1, hash2 = f"hash-{uuid.uuid4()}", f"hash-{uuid.uuid4()}"
        await refresh_token_repo.create(db_session, user.id, hash1, expires_at)
        await refresh_token_repo.create(db_session, user.id, hash2, expires_at)

        await refresh_token_repo.revoke_all_for_user(db_session, user.id)

        fetched1 = await refresh_token_repo.get_by_hash(db_session, hash1)
        fetched2 = await refresh_token_repo.get_by_hash(db_session, hash2)
        assert fetched1.revoked_at is not None
        assert fetched2.revoked_at is not None
    finally:
        await _cleanup(db_session, user.id)
