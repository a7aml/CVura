"""Deterministic, DB-free scoring of a career profile against a job's
keywords. Narrows the full profile down to the subset relevant to a job,
before any AI call is made. Pure functions only — no async, no DB, no AI."""

import re
from datetime import date

from app.schemas.resume import ResumeSelection, SelectedExperience, SelectedProject

MAX_EXPERIENCES = 5
MAX_PROJECTS = 3
MAX_PREFERRED_SKILLS = 5
MIN_SCORE_THRESHOLD = 0
RECENCY_MULTIPLIER = 1.1

_REQUIRED_WEIGHT_FIELDS = {"required_skills": 3, "technologies": 3, "keywords_ats": 3}
_PREFERRED_WEIGHT_FIELDS = {"preferred_skills": 1}

# Small, easy-to-extend map of common synonyms so e.g. a profile skill of
# "JS" matches a JD keyword of "JavaScript".
ALIAS_MAP = {
    "js": "javascript",
    "postgres": "postgresql",
    "k8s": "kubernetes",
}

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_MIN_DATE = date(1, 1, 1)


def normalize(term: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, apply alias map."""
    lowered = term.lower().strip()
    cleaned = _PUNCTUATION_RE.sub(" ", lowered)
    collapsed = " ".join(cleaned.split())
    return ALIAS_MAP.get(collapsed, collapsed)


def _normalize_blob(text: str) -> str:
    """Like normalize(), but alias-substitutes per token so multi-word blobs
    (bullets, titles) still match single-word JD keywords."""
    lowered = text.lower()
    cleaned = _PUNCTUATION_RE.sub(" ", lowered)
    tokens = [ALIAS_MAP.get(tok, tok) for tok in cleaned.split()]
    return " ".join(tokens)


def build_jd_keyword_weights(job_analysis: dict) -> dict[str, int]:
    """Weighted JD keyword set: required_skills/technologies/keywords_ats at
    weight 3, preferred_skills at weight 1."""
    weighted: dict[str, int] = {}
    for field, weight in {**_REQUIRED_WEIGHT_FIELDS, **_PREFERRED_WEIGHT_FIELDS}.items():
        for term in job_analysis.get(field) or []:
            key = normalize(term)
            if key:
                weighted[key] = max(weighted.get(key, 0), weight)
    return weighted


def _score_text(blob: str, jd_weighted: dict[str, int]) -> float:
    normalized_blob = _normalize_blob(blob)
    return float(sum(weight for keyword, weight in jd_weighted.items() if keyword in normalized_blob))


def score_skills(profile_skills: list[dict], jd_weighted: dict[str, int]) -> list[str]:
    """Include every matched weight-3 skill, plus the top N matched
    weight-1 skills, plus any profile skill flagged as core/primary."""
    required_matches: list[str] = []
    preferred_matches: list[str] = []
    core_matches: list[str] = []

    for skill in profile_skills:
        name = skill["name"]
        weight = jd_weighted.get(normalize(name))
        if skill.get("is_core"):
            core_matches.append(name)
        elif weight == 3:
            required_matches.append(name)
        elif weight == 1:
            preferred_matches.append(name)

    selected = required_matches + preferred_matches[:MAX_PREFERRED_SKILLS]
    for name in core_matches:
        if name not in selected:
            selected.append(name)
    return selected


def _experience_blob(experience: dict) -> str:
    parts = [experience.get("title", ""), experience.get("company", ""), *experience.get("bullets", [])]
    return " ".join(parts)


def _recency_key(item: dict) -> tuple[bool, date]:
    end_date = item.get("end_date")
    return (end_date is None, end_date or item.get("start_date") or _MIN_DATE)


def _most_recent(items: list[dict]) -> dict:
    return max(items, key=_recency_key)


def score_experiences(profile_experiences: list[dict], jd_weighted: dict[str, int]) -> list[SelectedExperience]:
    """Rank experiences by weighted JD-keyword overlap in bullets/title/company.
    The most recent/current role is always force-included and gets a +10%
    score multiplier. Falls back to most-recent-N if nothing scores above
    MIN_SCORE_THRESHOLD."""
    if not profile_experiences:
        return []

    most_recent = _most_recent(profile_experiences)
    scored = [(exp, _score_experience(exp, jd_weighted, most_recent)) for exp in profile_experiences]

    if all(score <= MIN_SCORE_THRESHOLD for _, score in scored):
        fallback = sorted(profile_experiences, key=_recency_key, reverse=True)[:MAX_EXPERIENCES]
        return [_to_selected_experience(exp, 0.0) for exp in fallback]

    return _select_top_experiences(scored, most_recent)


def _score_experience(experience: dict, jd_weighted: dict[str, int], most_recent: dict) -> float:
    score = _score_text(_experience_blob(experience), jd_weighted)
    return score * RECENCY_MULTIPLIER if experience is most_recent else score


def _select_top_experiences(scored: list[tuple[dict, float]], most_recent: dict) -> list[SelectedExperience]:
    scored = sorted(scored, key=lambda pair: pair[1], reverse=True)
    top = scored[:MAX_EXPERIENCES]

    if not any(exp is most_recent for exp, _ in top):
        recent_pair = next(pair for pair in scored if pair[0] is most_recent)
        top = top[: MAX_EXPERIENCES - 1] + [recent_pair]

    top.sort(key=lambda pair: _recency_key(pair[0]), reverse=True)
    return [_to_selected_experience(exp, score) for exp, score in top]


def _to_selected_experience(experience: dict, score: float) -> SelectedExperience:
    return SelectedExperience(
        experience_id=experience["id"], score=score, bullets_source=experience.get("bullets", [])
    )


def _project_blob(project: dict) -> str:
    parts = [project.get("name", ""), project.get("description") or "", *(project.get("tech_stack") or [])]
    return " ".join(parts)


def score_projects(profile_projects: list[dict], jd_weighted: dict[str, int]) -> list[SelectedProject]:
    """Same overlap-scoring pattern as experiences. Projects have no date
    field, so the zero-match fallback keeps the profile's own order."""
    if not profile_projects:
        return []

    scored = [(proj, _score_text(_project_blob(proj), jd_weighted)) for proj in profile_projects]

    if all(score <= MIN_SCORE_THRESHOLD for _, score in scored):
        fallback = profile_projects[:MAX_PROJECTS]
        return [SelectedProject(project_id=proj["id"], score=0.0) for proj in fallback]

    scored.sort(key=lambda pair: pair[1], reverse=True)
    top = scored[:MAX_PROJECTS]
    return [SelectedProject(project_id=proj["id"], score=score) for proj, score in top]


def select_resume_content(
    profile_skills: list[dict],
    profile_experiences: list[dict],
    profile_projects: list[dict],
    job_analysis: dict,
) -> ResumeSelection:
    jd_weighted = build_jd_keyword_weights(job_analysis)
    return ResumeSelection(
        selected_skills=score_skills(profile_skills, jd_weighted),
        selected_experiences=score_experiences(profile_experiences, jd_weighted),
        selected_projects=score_projects(profile_projects, jd_weighted),
    )
