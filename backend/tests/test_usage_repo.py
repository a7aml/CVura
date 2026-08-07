import uuid

from sqlalchemy import delete

from app.models.usage import Usage
from app.models.user import User
from app.repositories import usage_repo, user_repo


async def _make_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    return await user_repo.create_local_user(db_session, email, "hash")


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(Usage).where(Usage.user_id == user_id))
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_get_or_create_creates_row_with_defaults_when_none_exists(db_session):
    user = await _make_user(db_session)
    try:
        assert await usage_repo.get_by_user_id(db_session, user.id) is None

        usage = await usage_repo.get_or_create(db_session, user.id)

        assert usage.user_id == user.id
        assert usage.resumes_generated_count == 0
        assert usage.plan_limit == 3
    finally:
        await _cleanup(db_session, user.id)


async def test_get_or_create_returns_existing_row_without_resetting_it(db_session):
    user = await _make_user(db_session)
    try:
        first = await usage_repo.get_or_create(db_session, user.id)
        await usage_repo.increment_resumes_generated(db_session, user.id)

        second = await usage_repo.get_or_create(db_session, user.id)

        assert second.user_id == first.user_id
        assert second.resumes_generated_count == 1
    finally:
        await _cleanup(db_session, user.id)


async def test_increment_resumes_generated_is_cumulative(db_session):
    user = await _make_user(db_session)
    try:
        await usage_repo.get_or_create(db_session, user.id)

        await usage_repo.increment_resumes_generated(db_session, user.id)
        await usage_repo.increment_resumes_generated(db_session, user.id)
        await usage_repo.increment_resumes_generated(db_session, user.id)

        usage = await usage_repo.get_by_user_id(db_session, user.id)
        assert usage.resumes_generated_count == 3
    finally:
        await _cleanup(db_session, user.id)
