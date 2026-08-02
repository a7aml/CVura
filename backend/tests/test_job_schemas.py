import pytest
from pydantic import ValidationError

from app.schemas.job import MAX_RAW_DESCRIPTION_LENGTH, JobCreate


def test_job_create_rejects_raw_description_over_the_limit():
    with pytest.raises(ValidationError):
        JobCreate(
            source="linkedin",
            title="Engineer",
            raw_description="x" * (MAX_RAW_DESCRIPTION_LENGTH + 1),
        )


def test_job_create_allows_raw_description_at_the_limit():
    job = JobCreate(
        source="linkedin",
        title="Engineer",
        raw_description="x" * MAX_RAW_DESCRIPTION_LENGTH,
    )
    assert len(job.raw_description) == MAX_RAW_DESCRIPTION_LENGTH
