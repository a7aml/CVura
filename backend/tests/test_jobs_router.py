"""Router-level IDOR coverage: hits the real /jobs endpoints over HTTP with
a real DB-backed job, not a mocked service layer, to prove the ownership
check actually holds end-to-end and not just in the service unit tests."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.deps import get_current_user
from app.core.security import limiter
from app.main import app
from app.models.job import Job
from app.models.user import User
from app.repositories import job_repo, user_repo


async def _make_user(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    return await user_repo.create_local_user(db_session, email, "hash")


async def _cleanup(db_session, *user_ids):
    for user_id in user_ids:
        await db_session.execute(delete(Job).where(Job.user_id == user_id))
        await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


@pytest.fixture
def authed_client(db_session):
    # get_db is deliberately left un-overridden: TestClient drives the app
    # through its own event-loop context, so a request handler must open its
    # own AsyncSession (exactly what the real get_db dependency does) rather
    # than reusing this fixture's session object across loops — asyncpg
    # connections aren't safe to share that way.
    def _for(user):
        app.dependency_overrides[get_current_user] = lambda: user
        limiter.reset()
        return TestClient(app)

    yield _for
    app.dependency_overrides.clear()


async def test_get_job_rejects_id_owned_by_another_user(db_session, authed_client):
    owner = await _make_user(db_session)
    attacker = await _make_user(db_session)
    try:
        job = await job_repo.create_job(
            db_session, owner.id, source="linkedin", title="Owner's job", company=None, raw_description="x"
        )

        response = authed_client(attacker).get(f"/jobs/{job.id}")

        assert response.status_code == 404
    finally:
        await _cleanup(db_session, owner.id, attacker.id)


async def test_get_job_succeeds_for_the_owner(db_session, authed_client):
    owner = await _make_user(db_session)
    try:
        job = await job_repo.create_job(
            db_session, owner.id, source="linkedin", title="Owner's job", company=None, raw_description="x"
        )

        response = authed_client(owner).get(f"/jobs/{job.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(job.id)
    finally:
        await _cleanup(db_session, owner.id)


async def test_analyze_job_rejects_id_owned_by_another_user(db_session, authed_client):
    owner = await _make_user(db_session)
    attacker = await _make_user(db_session)
    try:
        job = await job_repo.create_job(
            db_session, owner.id, source="linkedin", title="Owner's job", company=None, raw_description="x"
        )

        response = authed_client(attacker).post(f"/jobs/{job.id}/analyze")

        assert response.status_code == 404
    finally:
        await _cleanup(db_session, owner.id, attacker.id)


async def test_list_jobs_never_returns_another_users_jobs(db_session, authed_client):
    owner = await _make_user(db_session)
    other = await _make_user(db_session)
    try:
        await job_repo.create_job(
            db_session, owner.id, source="linkedin", title="Owner's job", company=None, raw_description="x"
        )

        response = authed_client(other).get("/jobs")

        assert response.status_code == 200
        assert response.json() == []
    finally:
        await _cleanup(db_session, owner.id, other.id)
