import uuid

from sqlalchemy import delete

from app.models.job import Job
from app.models.user import User
from app.repositories import job_repo, user_repo


async def _make_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    return await user_repo.create_local_user(db_session, email, "hash")


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(Job).where(Job.user_id == user_id))
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_create_and_get_job(db_session):
    user = await _make_user(db_session)
    try:
        job = await job_repo.create_job(
            db_session,
            user.id,
            source="linkedin",
            title="Senior Product Designer",
            company="Acme Co",
            posting_url="https://www.linkedin.com/jobs/view/123",
            raw_description="We're looking for a designer...",
        )
        assert job.user_id == user.id
        assert job.parsed_json is None

        fetched = await job_repo.get_by_id(db_session, job.id)
        assert fetched is not None
        assert fetched.title == "Senior Product Designer"
    finally:
        await _cleanup(db_session, user.id)


async def test_list_by_user_orders_newest_first(db_session):
    user = await _make_user(db_session)
    try:
        first = await job_repo.create_job(
            db_session, user.id, source="linkedin", title="First", company=None, raw_description="x"
        )
        second = await job_repo.create_job(
            db_session, user.id, source="linkedin", title="Second", company=None, raw_description="y"
        )

        jobs = await job_repo.list_by_user(db_session, user.id)
        assert [j.id for j in jobs] == [second.id, first.id]
    finally:
        await _cleanup(db_session, user.id)


async def test_get_by_id_missing_returns_none(db_session):
    result = await job_repo.get_by_id(db_session, uuid.uuid4())
    assert result is None


async def test_list_by_user_empty_for_unknown_user(db_session):
    result = await job_repo.list_by_user(db_session, uuid.uuid4())
    assert result == []
