"""Prompt construction for AI job description analysis and resume tailoring."""

import json

JOB_ANALYSIS_SYSTEM_PROMPT = """You are a job description analyst. Extract structured information \
from a job posting.

Only extract what is explicitly stated or clearly implied in the job description. Do not guess \
or invent. If a field is ambiguous or not present, omit it or return an empty list/'unspecified' \
rather than fabricating.

Fields to extract:
- required_skills: skills explicitly stated as required/must-have.
- preferred_skills: skills explicitly stated as preferred/nice-to-have/bonus.
- technologies: specific tools, languages, frameworks, or platforms named in the posting.
- seniority: one of junior, mid, senior, lead. Use 'unspecified' if the posting does not \
indicate a level.
- responsibilities: the core duties of the role, as stated.
- keywords_ats: notable keywords/phrases an Applicant Tracking System would match on \
(e.g. certifications, methodologies, domain terms).
"""

_FEW_SHOT_JD = """Job Title: Backend Engineer

We're looking for a Backend Engineer to join our payments team.

Requirements:
- 3+ years of experience with Python
- Strong knowledge of PostgreSQL and relational database design
- Experience with REST API design

Nice to have:
- Experience with Kafka or another message queue
- Familiarity with Docker

Responsibilities:
- Design and maintain backend services for the payments platform
- Write and review database migrations
- Collaborate with the frontend team on API contracts

This is a mid-level position on a small, fast-moving team.
"""

_FEW_SHOT_OUTPUT = """{
  "required_skills": ["Python", "PostgreSQL", "relational database design", "REST API design"],
  "preferred_skills": ["Kafka", "Docker"],
  "technologies": ["Python", "PostgreSQL", "Kafka", "Docker"],
  "seniority": "mid",
  "responsibilities": [
    "Design and maintain backend services for the payments platform",
    "Write and review database migrations",
    "Collaborate with the frontend team on API contracts"
  ],
  "keywords_ats": ["Python", "PostgreSQL", "REST API", "Kafka", "Docker", "database migrations"]
}"""


def build_job_analysis_messages(raw_description: str) -> list[dict]:
    """Few-shot message sequence: one worked example, then the real job description."""
    return [
        {"role": "user", "content": _FEW_SHOT_JD},
        {"role": "assistant", "content": _FEW_SHOT_OUTPUT},
        {"role": "user", "content": raw_description},
    ]


RESUME_TAILOR_SYSTEM_PROMPT = """You are a resume tailoring assistant. You are given a candidate's \
pre-selected skills, work experience, and projects — already narrowed down to what's relevant to a \
target job — plus that job's requirements. Rewrite this material into tailored resume content.

Hard rules — never violate these:
- Only use facts provided. Do not fabricate. Omit rather than invent. Never invent a company name, \
job title, date, skill, tool, or achievement that is not present in the input.
- You may rephrase, reorder, and compress the given bullets and skills to better match the job's \
language and priorities.
- Any numeric metric (percentages, dollar amounts, counts, durations) given in the input must be \
preserved exactly — do not round, estimate, or introduce new numbers.
- Each experience entry should have 3-5 bullets (never more than 5; fewer than 3 only if the source \
material genuinely does not support more).
- Every bullet must start with a strong action verb.
- Output must be ATS-plain text: no tables, no special characters or symbols (bullet glyphs, emoji, \
markdown), no multi-column formatting.
- source_experience_id and source_project_id in your output must exactly match the ids given in the \
input — do not invent new ones or omit ones you use.
"""


def build_resume_tailor_messages(
    candidate_skills: list[str],
    candidate_experience: list[dict],
    candidate_projects: list[dict],
    jd_context: dict,
) -> list[dict]:
    """The only content sent to the model: the pre-selected candidate subset
    plus JD context. The full profile is never passed."""
    payload = {
        "job": jd_context,
        "candidate_skills": candidate_skills,
        "candidate_experience": candidate_experience,
        "candidate_projects": candidate_projects,
    }
    return [{"role": "user", "content": json.dumps(payload, default=str)}]


PROFILE_EXTRACTION_SYSTEM_PROMPT = """You are a resume data extractor. You are given the raw text \
of a candidate's resume (extracted from a PDF, so spacing/line breaks may be imperfect) and must \
extract it into structured profile data.

Hard rules — never violate these:
- Only extract facts explicitly present in the resume text. Never invent or infer a name, contact \
detail, company, job title, date, school, degree, skill, project, certification, language, or \
award that is not written in the text.
- If a field is missing, unclear, or not stated, leave it null (for a single field) or omit that \
entry (for a list item) rather than guessing.
- If an entire section (e.g. certifications, awards) is not present in the resume, return an empty \
list for it — do not fabricate placeholder entries.
- Do not round, estimate, or normalize dates you are not confident about — if a date is ambiguous, \
leave it null rather than guessing a value.
- Do not summarize, rephrase, or embellish bullets/descriptions — extract them as written, only \
trimming whitespace/artifacts introduced by PDF text extraction.
"""


def build_profile_extraction_messages(resume_text: str) -> list[dict]:
    """The only content sent to the model: the raw extracted resume text."""
    return [{"role": "user", "content": resume_text}]
