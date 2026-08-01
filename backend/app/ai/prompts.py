"""Prompt construction for AI job description analysis."""

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
