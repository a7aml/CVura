import uuid

import pytest
from sqlalchemy import text

from app.models.user import User
from app.repositories import (
    awards_repo,
    certifications_repo,
    education_repo,
    experiences_repo,
    languages_repo,
    profile_repo,
    projects_repo,
    skills_repo,
    user_repo,
)

CHILD_REPOS = [
    (education_repo, "education", {"school": "Test University", "degree": "BSc"}),
    (experiences_repo, "experiences", {"title": "Engineer", "company": "Acme"}),
    (projects_repo, "projects", {"name": "Test Project"}),
    (skills_repo, "skills", {"name": "Python"}),
    (certifications_repo, "certifications", {"name": "AWS Cert"}),
    (languages_repo, "languages", {"name": "English"}),
    (awards_repo, "awards", {"title": "Employee of the month"}),
]


async def _make_user_and_profile(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    user = await user_repo.create_local_user(db_session, email, "hash")
    profile = await profile_repo.create_profile(db_session, user.id, full_name="Test User")
    return user, profile


async def _cleanup(db_session, user):
    for table in (
        "education",
        "experiences",
        "projects",
        "skills",
        "certifications",
        "languages",
        "awards",
    ):
        await db_session.execute(
            text(f"delete from {table} where profile_id in (select id from profiles where user_id = :uid)"),
            {"uid": str(user.id)},
        )
    await db_session.execute(text("delete from profiles where user_id = :uid"), {"uid": str(user.id)})
    await db_session.execute(text("delete from users where id = :uid"), {"uid": str(user.id)})
    await db_session.commit()


@pytest.mark.parametrize("repo,table_name,fields", CHILD_REPOS)
async def test_child_repo_crud(db_session, repo, table_name, fields):
    user, profile = await _make_user_and_profile(db_session)
    try:
        item = await repo.create(db_session, profile.id, **fields)
        assert item.profile_id == profile.id

        listed = await repo.list_by_profile(db_session, profile.id)
        assert any(i.id == item.id for i in listed)

        fetched = await repo.get_by_id(db_session, item.id)
        assert fetched is not None

        updated = await repo.update(db_session, fetched, **fields)
        assert updated.id == item.id

        await repo.delete(db_session, updated)
        assert await repo.get_by_id(db_session, item.id) is None
    finally:
        await _cleanup(db_session, user)
