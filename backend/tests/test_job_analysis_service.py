import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services import job_analysis_service


class FakeJob:
    def __init__(self, user_id, title="Senior Product Designer"):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.title = title


@patch("app.services.job_analysis_service.job_repo")
async def test_create_job(mock_repo):
    user_id = uuid.uuid4()
    created = FakeJob(user_id)
    mock_repo.create_job = AsyncMock(return_value=created)

    data = {"source": "linkedin", "title": "Senior Product Designer", "raw_description": "..."}
    result = await job_analysis_service.create_job(None, user_id, data)

    assert result is created
    mock_repo.create_job.assert_awaited_once_with(None, user_id, **data)


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_success(mock_repo):
    user_id = uuid.uuid4()
    existing = FakeJob(user_id)
    mock_repo.get_by_id = AsyncMock(return_value=existing)

    result = await job_analysis_service.get_job(None, user_id, existing.id)
    assert result is existing


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_missing_raises(mock_repo):
    mock_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(job_analysis_service.JobNotFound):
        await job_analysis_service.get_job(None, uuid.uuid4(), uuid.uuid4())


@patch("app.services.job_analysis_service.job_repo")
async def test_get_job_owned_by_another_user_raises(mock_repo):
    other_users_job = FakeJob(uuid.uuid4())
    mock_repo.get_by_id = AsyncMock(return_value=other_users_job)

    with pytest.raises(job_analysis_service.JobNotFound):
        await job_analysis_service.get_job(None, uuid.uuid4(), other_users_job.id)


@patch("app.services.job_analysis_service.job_repo")
async def test_list_jobs(mock_repo):
    user_id = uuid.uuid4()
    jobs = [FakeJob(user_id), FakeJob(user_id)]
    mock_repo.list_by_user = AsyncMock(return_value=jobs)

    result = await job_analysis_service.list_jobs(None, user_id)
    assert result is jobs
