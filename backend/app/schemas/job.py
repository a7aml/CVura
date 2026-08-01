import datetime as dt
import uuid
from typing import Literal

from pydantic import BaseModel

_OUT_CONFIG = {"from_attributes": True}


class JobCreate(BaseModel):
    source: str
    title: str
    company: str | None = None
    posting_url: str | None = None
    raw_description: str


class JobOut(JobCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    parsed_json: dict | None = None
    created_at: dt.datetime
    model_config = _OUT_CONFIG


class JobAnalysis(BaseModel):
    """AI-extracted structure of a job description. Source of truth for both the
    model's structured-output schema and validation of its response."""

    required_skills: list[str]
    preferred_skills: list[str]
    technologies: list[str]
    seniority: Literal["junior", "mid", "senior", "lead", "unspecified"]
    responsibilities: list[str]
    keywords_ats: list[str]
