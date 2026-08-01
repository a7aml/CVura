import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

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
