from pydantic import BaseModel

from app.schemas.profile import (
    AwardIn,
    CertificationIn,
    EducationIn,
    ExperienceIn,
    LanguageIn,
    ProjectIn,
    SkillIn,
)

# Generous cap on extracted resume text, well below anything a real resume
# needs, to bound AI-provider cost/abuse — mirrors MAX_RAW_DESCRIPTION_LENGTH
# in schemas/job.py.
MAX_RESUME_TEXT_LENGTH = 20_000

# Reject the uploaded file before it's even read, matching the frontend's cap.
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024


class PersonalInfoExtract(BaseModel):
    """Same fields as ProfileCreate, but all optional — the AI may not find
    every field in a given resume, and a missing field must stay null rather
    than being guessed."""

    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    desired_title: str | None = None
    summary: str | None = None
    career_objective: str | None = None


class ProfileExtractionOutput(BaseModel):
    """AI-extracted structure of a resume. Source of truth for both the
    model's structured-output schema and validation of its response.
    Reuses the same *In section schemas as the manual wizard so extracted
    data has exactly the same shape as manually-entered data."""

    personal_info: PersonalInfoExtract
    education: list[EducationIn] = []
    experiences: list[ExperienceIn] = []
    projects: list[ProjectIn] = []
    skills: list[SkillIn] = []
    certifications: list[CertificationIn] = []
    languages: list[LanguageIn] = []
    awards: list[AwardIn] = []
