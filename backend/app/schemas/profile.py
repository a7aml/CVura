import datetime as dt
import uuid

from pydantic import BaseModel

_OUT_CONFIG = {"from_attributes": True}


class EducationIn(BaseModel):
    school: str
    degree: str | None = None
    field: str | None = None
    start_date: dt.date | None = None
    end_date: dt.date | None = None


class EducationOut(EducationIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class ExperienceIn(BaseModel):
    title: str
    company: str
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    bullets: list[str] = []


class ExperienceOut(ExperienceIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class ProjectIn(BaseModel):
    name: str
    description: str | None = None
    tech_stack: list[str] = []
    link: str | None = None


class ProjectOut(ProjectIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class SkillIn(BaseModel):
    name: str
    category: str | None = None


class SkillOut(SkillIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class CertificationIn(BaseModel):
    name: str
    issuer: str | None = None
    date_earned: dt.date | None = None


class CertificationOut(CertificationIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class LanguageIn(BaseModel):
    name: str
    proficiency: str | None = None


class LanguageOut(LanguageIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class AwardIn(BaseModel):
    title: str
    issuer: str | None = None
    date: dt.date | None = None


class AwardOut(AwardIn):
    id: uuid.UUID
    model_config = _OUT_CONFIG


class ProfileCreate(BaseModel):
    full_name: str
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    desired_title: str | None = None
    summary: str | None = None
    career_objective: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    desired_title: str | None = None
    summary: str | None = None
    career_objective: str | None = None


class ProfileOut(ProfileCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: dt.datetime
    updated_at: dt.datetime
    model_config = _OUT_CONFIG


class FullProfileOut(ProfileOut):
    education: list[EducationOut] = []
    experiences: list[ExperienceOut] = []
    projects: list[ProjectOut] = []
    skills: list[SkillOut] = []
    certifications: list[CertificationOut] = []
    languages: list[LanguageOut] = []
    awards: list[AwardOut] = []
