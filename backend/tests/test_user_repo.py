import uuid

from sqlalchemy import delete

from app.models.user import User
from app.repositories import user_repo


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_create_and_get_local_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    user = await user_repo.create_local_user(db_session, email, "hashed-value")
    try:
        assert user.id is not None
        assert user.password_hash == "hashed-value"

        fetched = await user_repo.get_by_email(db_session, email)
        assert fetched is not None
        assert fetched.id == user.id

        fetched_by_id = await user_repo.get_by_id(db_session, user.id)
        assert fetched_by_id.email == email
    finally:
        await _cleanup(db_session, user.id)


async def test_create_and_get_google_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    google_sub = str(uuid.uuid4())
    user = await user_repo.create_google_user(db_session, email, google_sub)
    try:
        assert user.google_sub == google_sub
        assert user.password_hash is None

        fetched = await user_repo.get_by_google_sub(db_session, google_sub)
        assert fetched is not None
        assert fetched.id == user.id
    finally:
        await _cleanup(db_session, user.id)


async def test_get_by_email_missing_returns_none(db_session):
    result = await user_repo.get_by_email(db_session, f"missing-{uuid.uuid4()}@example.com")
    assert result is None
