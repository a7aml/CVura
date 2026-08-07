import uuid

from app.ai import client as ai_client
from app.core.config import settings
from app.repositories import profile_repo, resume_repo, usage_repo, user_repo
from app.schemas.resume import ResumeTailorOutput
from app.services import job_analysis_service, pdf_service, resume_selection_service


class ProfileNotFound(Exception):
    pass


class JobNotAnalyzed(Exception):
    pass


class ResumeTailorError(Exception):
    pass


class AIServiceUnavailable(Exception):
    pass


class TailorInputTooLarge(Exception):
    pass


class QuotaExceeded(Exception):
    pass


async def _enforce_quota(db, user) -> None:
    """Free-plan accounts are capped at settings.free_tier_resume_limit
    lifetime generations; Pro and comped accounts are unlimited.

    NOTE: FREE_TIER_RESUME_LIMIT is temporarily set very high for
    pre-billing testing (Stripe integration is Build Order step 8).
    Reset it to the real free-tier limit (3) once billing ships."""
    if user.plan != "free" or user.comped_reason is not None:
        return
    usage = await usage_repo.get_or_create(db, user.id)
    if usage.resumes_generated_count >= settings.free_tier_resume_limit:
        raise QuotaExceeded()


async def tailor_resume(db, user_id: uuid.UUID, job_id: uuid.UUID):
    """Orchestrates: fetch profile + analyzed job -> deterministic selection
    -> AI tailoring call -> persist as a new resume version. Returns
    (ResumeTailorOutput, Resume)."""
    job = await job_analysis_service.get_job(db, user_id, job_id)
    if job.parsed_json is None:
        raise JobNotAnalyzed()

    user = await user_repo.get_by_id(db, user_id)
    await _enforce_quota(db, user)

    profile = await profile_repo.get_by_user_id(db, user_id)
    if profile is None:
        raise ProfileNotFound()

    selection = resume_selection_service.select_resume_content(
        profile_skills=[{"name": s.name} for s in profile.skills],
        profile_experiences=[_experience_to_dict(e) for e in profile.experiences],
        profile_projects=[_project_to_dict(p) for p in profile.projects],
        job_analysis=job.parsed_json,
    )
    candidate_experience, candidate_projects = _build_candidate_payload(profile, selection)
    jd_context = _build_jd_context(job)

    try:
        tailored = await _tailor_with_retry(
            selection.selected_skills, candidate_experience, candidate_projects, jd_context
        )
    except ai_client.TailorInputTooLarge as exc:
        raise TailorInputTooLarge(str(exc)) from exc

    resume = await resume_repo.create_resume(
        db, user_id, job_id, tailored.model_dump(mode="json"), tailored.match_explanation
    )
    resume = await _attach_pdf(db, user_id, resume, profile, tailored)
    await usage_repo.increment_resumes_generated(db, user_id)
    return tailored, resume


async def _attach_pdf(db, user_id: uuid.UUID, resume, profile, tailored: ResumeTailorOutput):
    """Best-effort: a PDF failure never fails the /tailor request. On
    success, persists the R2 object key; on failure, the resume keeps
    pdf_key=None. The router turns the stored key into a presigned download
    URL — nothing here ever produces a permanent public link."""
    user = await user_repo.get_by_id(db, user_id)
    contact = _build_contact(profile, user)
    education = [_education_to_dict(e) for e in profile.education]
    certifications = [_certification_to_dict(c) for c in profile.certifications]

    pdf_key = await pdf_service.generate_and_upload_pdf(
        user_id, resume.id, tailored, contact, education, certifications
    )
    if pdf_key is None:
        return resume
    return await resume_repo.update_pdf_key(db, resume.id, user_id, pdf_key) or resume


def _build_contact(profile, user) -> dict:
    return {
        "full_name": profile.full_name,
        "email": user.email,
        "phone": profile.phone,
        "location": profile.location,
        "linkedin_url": profile.linkedin_url,
    }


def _education_to_dict(education) -> dict:
    return {
        "school": education.school,
        "degree": education.degree,
        "field": education.field,
        "start_date": education.start_date,
        "end_date": education.end_date,
    }


def _certification_to_dict(certification) -> dict:
    return {
        "name": certification.name,
        "issuer": certification.issuer,
        "date_earned": certification.date_earned,
    }


async def _tailor_with_retry(
    candidate_skills: list[str], candidate_experience: list[dict], candidate_projects: list[dict], jd_context: dict
) -> ResumeTailorOutput:
    for attempt in range(2):
        try:
            return await ai_client.tailor_resume(candidate_skills, candidate_experience, candidate_projects, jd_context)
        except ai_client.AIResponseInvalid:
            if attempt == 1:
                raise ResumeTailorError("AI resume tailoring failed validation twice") from None
        except ai_client.AIProviderError as exc:
            if attempt == 1:
                raise AIServiceUnavailable("AI provider is temporarily unavailable") from exc


def _experience_to_dict(experience) -> dict:
    return {
        "id": experience.id,
        "title": experience.title,
        "company": experience.company,
        "bullets": experience.bullets,
        "start_date": experience.start_date,
        "end_date": experience.end_date,
    }


def _project_to_dict(project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "tech_stack": project.tech_stack,
    }


def _build_candidate_payload(profile, selection) -> tuple[list[dict], list[dict]]:
    experiences_by_id = {e.id: e for e in profile.experiences}
    projects_by_id = {p.id: p for p in profile.projects}

    candidate_experience = [
        _candidate_experience_entry(experiences_by_id[selected.experience_id], selected)
        for selected in selection.selected_experiences
    ]
    candidate_projects = [
        _candidate_project_entry(projects_by_id[selected.project_id]) for selected in selection.selected_projects
    ]
    return candidate_experience, candidate_projects


def _candidate_experience_entry(experience, selected) -> dict:
    return {
        "id": str(experience.id),
        "title": experience.title,
        "company": experience.company,
        "start_date": experience.start_date,
        "end_date": experience.end_date,
        "bullets": selected.bullets_source,
    }


def _candidate_project_entry(project) -> dict:
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "tech_stack": project.tech_stack,
    }


def _build_jd_context(job) -> dict:
    analysis = job.parsed_json
    return {
        "title": job.title,
        "seniority": analysis.get("seniority"),
        "required_skills": analysis.get("required_skills", []),
        "technologies": analysis.get("technologies", []),
        "keywords_ats": analysis.get("keywords_ats", []),
    }
