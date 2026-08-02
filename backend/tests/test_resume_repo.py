import uuid

from sqlalchemy import delete

from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.repositories import job_repo, resume_repo, user_repo


async def _make_user_and_job(db_session):
    email = f"test-{uuid.uuid4()}@example.com"
    user = await user_repo.create_local_user(db_session, email, "hash")
    job = await job_repo.create_job(
        db_session, user.id, source="linkedin", title="Engineer", company=None, raw_description="x"
    )
    return user, job


async def _cleanup(db_session, user_id):
    await db_session.execute(delete(Resume).where(Resume.user_id == user_id))
    await db_session.execute(delete(Job).where(Job.user_id == user_id))
    await db_session.execute(delete(User).where(User.id == user_id))
    await db_session.commit()


async def test_create_resume_starts_at_version_one(db_session):
    user, job = await _make_user_and_job(db_session)
    try:
        resume = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})
        assert resume.version == 1
        assert resume.content_json == {"summary": "v1"}
    finally:
        await _cleanup(db_session, user.id)


async def test_create_resume_increments_version_per_job_and_user(db_session):
    user, job = await _make_user_and_job(db_session)
    try:
        first = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})
        second = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v2"})

        assert first.version == 1
        assert second.version == 2
        assert first.id != second.id
    finally:
        await _cleanup(db_session, user.id)


async def test_get_resumes_by_job_orders_newest_version_first(db_session):
    user, job = await _make_user_and_job(db_session)
    try:
        first = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})
        second = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v2"})

        resumes = await resume_repo.get_resumes_by_job(db_session, job.id, user.id)

        assert [r.id for r in resumes] == [second.id, first.id]
    finally:
        await _cleanup(db_session, user.id)


async def test_get_resumes_by_job_excludes_other_users_resumes(db_session):
    user, job = await _make_user_and_job(db_session)
    other_user, _ = await _make_user_and_job(db_session)
    try:
        await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})

        resumes = await resume_repo.get_resumes_by_job(db_session, job.id, other_user.id)

        assert resumes == []
    finally:
        await _cleanup(db_session, user.id)
        await _cleanup(db_session, other_user.id)


async def test_update_pdf_url_sets_url_for_owned_resume(db_session):
    user, job = await _make_user_and_job(db_session)
    try:
        resume = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})

        updated = await resume_repo.update_pdf_url(db_session, resume.id, user.id, "https://cdn.example.com/r.pdf")

        assert updated is not None
        assert updated.pdf_url == "https://cdn.example.com/r.pdf"
    finally:
        await _cleanup(db_session, user.id)


async def test_update_pdf_url_returns_none_for_other_users_resume(db_session):
    user, job = await _make_user_and_job(db_session)
    other_user, _ = await _make_user_and_job(db_session)
    try:
        resume = await resume_repo.create_resume(db_session, user.id, job.id, {"summary": "v1"})

        result = await resume_repo.update_pdf_url(db_session, resume.id, other_user.id, "https://cdn.example.com/r.pdf")

        assert result is None
        fetched = await resume_repo.get_resumes_by_job(db_session, job.id, user.id)
        assert fetched[0].pdf_url is None
    finally:
        await _cleanup(db_session, user.id)
        await _cleanup(db_session, other_user.id)
