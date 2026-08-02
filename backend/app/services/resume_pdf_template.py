"""Builds the ATS-safe Typst source for a tailored resume: single column,
Times New Roman, black-on-white, plain bullets, no tables/images/icons.
Pure string building — no I/O, no AI call. Every interpolated value is
escaped so profile/JD content (user-controlled) can never inject Typst
markup or code."""

import datetime as dt

from app.schemas.resume import ExperienceEntry, ProjectEntry, ResumeTailorOutput

_ESCAPE_CHARS = "\\*_`$#<>@[]"

_PRELUDE = """\
#set page(margin: (x: 2cm, y: 1.8cm), fill: white)
#set text(font: "Times New Roman", size: 10.5pt, fill: black)
#set par(justify: false)
#set heading(numbering: none)
"""


def escape_typst(text: str) -> str:
    """Escapes Typst markup control characters and collapses newlines, so
    interpolated content can't break out of plain text into markup/code."""
    cleaned = text.replace("\r", " ").replace("\n", " ")
    for ch in _ESCAPE_CHARS:
        cleaned = cleaned.replace(ch, "\\" + ch)
    return cleaned


def _format_date(value: dt.date | None) -> str:
    return value.strftime("%b %Y") if value else ""


def _format_date_range(start: dt.date | None, end: dt.date | None) -> str:
    start_label = _format_date(start) or "Unknown"
    end_label = _format_date(end) if end else "Present"
    return f"{start_label} - {end_label}"


def _contact_line(contact: dict) -> str:
    fields = ("email", "phone", "location", "linkedin_url")
    parts = [contact.get(field) for field in fields]
    return " | ".join(escape_typst(p) for p in parts if p)


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {escape_typst(item)}" for item in items)


def _summary_section(summary: str) -> str:
    return f"== Summary\n{escape_typst(summary)}\n"


def _skills_section(skills: list[str]) -> str:
    if not skills:
        return ""
    return f"== Skills\n{escape_typst(', '.join(skills))}\n"


def _experience_entry(entry: ExperienceEntry) -> str:
    header = f"=== {escape_typst(entry.title)} -- {escape_typst(entry.company)}"
    date_range = _format_date_range(entry.start_date, entry.end_date)
    return f"{header}\n{date_range}\n{_bullets(entry.bullets)}\n"


def _experience_section(experience: list[ExperienceEntry]) -> str:
    if not experience:
        return ""
    return "== Experience\n" + "\n".join(_experience_entry(e) for e in experience)


def _project_entry(project: ProjectEntry) -> str:
    return f"=== {escape_typst(project.name)}\n{_bullets(project.bullets)}\n"


def _projects_section(projects: list[ProjectEntry]) -> str:
    if not projects:
        return ""
    return "== Projects\n" + "\n".join(_project_entry(p) for p in projects)


def _education_entry(entry: dict) -> str:
    header = f"=== {escape_typst(entry['school'])}"
    degree_field = ", ".join(escape_typst(v) for v in (entry.get("degree"), entry.get("field")) if v)
    date_range = _format_date_range(entry.get("start_date"), entry.get("end_date"))
    return f"{header}\n{degree_field}\n{date_range}\n"


def _education_section(education: list[dict]) -> str:
    if not education:
        return ""
    return "== Education\n" + "\n".join(_education_entry(e) for e in education)


def _certification_line(cert: dict) -> str:
    parts = [p for p in (cert["name"], cert.get("issuer")) if p]
    label = " -- ".join(escape_typst(p) for p in parts)
    date = _format_date(cert.get("date_earned"))
    return f"- {label}{f' ({date})' if date else ''}"


def _certifications_section(certifications: list[dict]) -> str:
    if not certifications:
        return ""
    return "== Certifications\n" + "\n".join(_certification_line(c) for c in certifications)


def build_resume_typst(
    tailored: ResumeTailorOutput,
    contact: dict,
    education: list[dict],
    certifications: list[dict],
) -> str:
    sections = [
        f"= {escape_typst(contact['full_name'])}",
        _contact_line(contact),
        "",
        _summary_section(tailored.summary),
        _skills_section(tailored.skills),
        _experience_section(tailored.experience),
        _projects_section(tailored.projects),
        _education_section(education),
        _certifications_section(certifications),
    ]
    body = "\n".join(section for section in sections if section)
    return _PRELUDE + "\n" + body
