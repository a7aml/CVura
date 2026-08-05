"""Router-level IDOR coverage for /profile/education: hits the real HTTP
endpoint with a real DB-backed profile item, not a mocked service layer.
profile_sections_service applies the identical _assert_owned check to every
other section (experiences, projects, skills, certifications, languages,
awards) via the same helper, so this one section stands in for all of them."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.deps import get_current_user
from app.core.security import limiter
from app.main import app
from app.models.education import Education
from app.models.profile import Profile
from app.models.user import User
from app.repositories import education_repo, profile_repo, user_repo


async def _make_user_with_profile(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    user = await user_repo.create_local_user(db_session, email, "hash")
    profile = await profile_repo.create_profile(db_session, user.id, full_name="Test User")
    return user, profile


async def _cleanup(db_session, *user_ids):
    for user_id in user_ids:
        profile = await profile_repo.get_by_user_id(db_session, user_id)
        if profile is not None:
            await db_session.execute(delete(Education).where(Education.profile_id == profile.id))
            await db_session.execute(delete(Profile).where(Profile.id == profile.id))
        await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


@pytest.fixture
def authed_client(db_session):
    # get_db is deliberately left un-overridden — see test_jobs_router.py
    # for why (cross-event-loop asyncpg session reuse is unsafe here).
    def _for(user):
        app.dependency_overrides[get_current_user] = lambda: user
        limiter.reset()
        return TestClient(app)

    yield _for
    app.dependency_overrides.clear()


async def test_update_education_rejects_item_owned_by_another_user(db_session, authed_client):
    owner, owner_profile = await _make_user_with_profile(db_session)
    attacker, _ = await _make_user_with_profile(db_session)
    try:
        item = await education_repo.create(db_session, owner_profile.id, school="State University")

        response = authed_client(attacker).patch(f"/profile/education/{item.id}", json={"school": "Hijacked U"})

        assert response.status_code == 404
    finally:
        await _cleanup(db_session, owner.id, attacker.id)


async def test_delete_education_rejects_item_owned_by_another_user(db_session, authed_client):
    owner, owner_profile = await _make_user_with_profile(db_session)
    attacker, _ = await _make_user_with_profile(db_session)
    try:
        item = await education_repo.create(db_session, owner_profile.id, school="State University")

        response = authed_client(attacker).delete(f"/profile/education/{item.id}")

        assert response.status_code == 404
        still_there = await education_repo.get_by_id(db_session, item.id)
        assert still_there is not None
    finally:
        await _cleanup(db_session, owner.id, attacker.id)


async def test_update_education_succeeds_for_the_owner(db_session, authed_client):
    owner, owner_profile = await _make_user_with_profile(db_session)
    try:
        item = await education_repo.create(db_session, owner_profile.id, school="State University")

        response = authed_client(owner).patch(f"/profile/education/{item.id}", json={"school": "Renamed U"})

        assert response.status_code == 200
        assert response.json()["school"] == "Renamed U"
    finally:
        await _cleanup(db_session, owner.id)
