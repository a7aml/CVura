import hashlib
import uuid

from app.ai import client as ai_client
from app.repositories import job_repo


class JobNotFound(Exception):
    pass


class JobAnalysisError(Exception):
    pass


class AIServiceUnavailable(Exception):
    pass


class JobDescriptionTooLong(Exception):
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


# --- AI analysis (Build Order step 4) ---


def _hash_jd(raw_description: str) -> str:
    return hashlib.sha256(raw_description.encode("utf-8")).hexdigest()


async def analyze_job(db, user_id: uuid.UUID, job_id: uuid.UUID):
    job = await get_job(db, user_id, job_id)
    jd_hash = _hash_jd(job.raw_description)

    cached = await job_repo.get_analyzed_by_hash(db, jd_hash)
    if cached is not None:
        return await job_repo.set_analysis(db, job, cached.parsed_json, jd_hash)

    try:
        analysis = await _analyze_with_retry(job.raw_description)
    except ai_client.RawDescriptionTooLong as exc:
        raise JobDescriptionTooLong(str(exc)) from exc
    return await job_repo.set_analysis(db, job, analysis.model_dump(), jd_hash)


async def _analyze_with_retry(raw_description: str):
    for attempt in range(2):
        try:
            return await ai_client.analyze_job_description(raw_description)
        except ai_client.AIResponseInvalid:
            if attempt == 1:
                raise JobAnalysisError("AI job analysis failed validation twice") from None
        except ai_client.AIProviderError as exc:
            if attempt == 1:
                raise AIServiceUnavailable("AI provider is temporarily unavailable") from exc
