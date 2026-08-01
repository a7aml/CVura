import uuid

from app.repositories import job_repo


class JobNotFound(Exception):
    pass


# --- storage (Build Order step 3: job description extraction) ---


async def create_job(db, user_id: uuid.UUID, data: dict):
    return await job_repo.create_job(db, user_id, **data)


async def get_job(db, user_id: uuid.UUID, job_id: uuid.UUID):
    job = await job_repo.get_by_id(db, job_id)
    if job is None or job.user_id != user_id:
        raise JobNotFound()
    return job


async def list_jobs(db, user_id: uuid.UUID):
    return await job_repo.list_by_user(db, user_id)


# --- AI analysis (Build Order step 4 — not started yet) ---
