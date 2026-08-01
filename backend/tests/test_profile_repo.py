import uuid

from sqlalchemy import delete

from app.models.profile import Profile
from app.models.user import User
from app.repositories import profile_repo, user_repo


async def _make_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    return await user_repo.create_local_user(db_session, email, "hash")


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(Profile).where(Profile.user_id == user_id))
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_create_get_update_profile(db_session):
    user = await _make_user(db_session)
    try:
        profile = await profile_repo.create_profile(db_session, user.id, full_name="Jordan Diaz")
        assert profile.full_name == "Jordan Diaz"
        assert profile.user_id == user.id

        fetched = await profile_repo.get_by_user_id(db_session, user.id)
        assert fetched is not None
        assert fetched.id == profile.id
        assert fetched.education == []

        updated = await profile_repo.update_profile(db_session, fetched, summary="Updated summary")
        assert updated.summary == "Updated summary"
        assert updated.full_name == "Jordan Diaz"
    finally:
        await _cleanup(db_session, user.id)


async def test_get_by_user_id_missing_returns_none(db_session):
    result = await profile_repo.get_by_user_id(db_session, uuid.uuid4())
    assert result is None
