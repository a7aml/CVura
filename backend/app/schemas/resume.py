import datetime as dt
import uuid

from pydantic import BaseModel, Field


class SelectedExperience(BaseModel):
    """A profile experience chosen by the selection service, with the raw
    bullets it was chosen for — the only experience content passed to AI."""

    experience_id: uuid.UUID
    score: float
    bullets_source: list[str]


class SelectedProject(BaseModel):
    project_id: uuid.UUID
    score: float


class ResumeSelection(BaseModel):
    """Deterministic, pre-AI selection result: which profile subset is
    relevant to a given job description."""

    selected_skills: list[str]
    selected_experiences: list[SelectedExperience]
    selected_projects: list[SelectedProject]


class ExperienceEntry(BaseModel):
    source_experience_id: uuid.UUID
    company: str
    title: str
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    bullets: list[str] = Field(..., min_length=1, max_length=5)


class ProjectEntry(BaseModel):
    source_project_id: uuid.UUID
    name: str
    bullets: list[str]


class ResumeTailorOutput(BaseModel):
    """AI structured output schema for tailored resume content."""

    summary: str
    skills: list[str]
    experience: list[ExperienceEntry]
    projects: list[ProjectEntry]
    match_explanation: str


class ResumeTailorResponse(ResumeTailorOutput):
    resume_id: uuid.UUID
    version: int
