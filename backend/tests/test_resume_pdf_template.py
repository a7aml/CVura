import datetime as dt
import uuid

from app.schemas.resume import ExperienceEntry, ProjectEntry, ResumeTailorOutput
from app.services.resume_pdf_template import build_resume_typst, escape_typst

CONTACT = {
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "555-1234",
    "location": "NYC",
    "linkedin_url": "linkedin.com/in/jane",
}


def _output(**overrides):
    defaults = dict(
        summary="Experienced backend engineer.",
        skills=["Python", "PostgreSQL"],
        experience=[
            ExperienceEntry(
                source_experience_id=uuid.uuid4(),
                company="Acme",
                title="Backend Engineer",
                start_date=dt.date(2022, 1, 1),
                end_date=None,
                bullets=["Built REST APIs"],
            )
        ],
        projects=[ProjectEntry(source_project_id=uuid.uuid4(), name="Side Project", bullets=["Did a thing"])],
        match_explanation="Strong Python overlap.",
    )
    defaults.update(overrides)
    return ResumeTailorOutput(**defaults)


def test_escape_typst_escapes_all_control_characters():
    raw = "C# * _ ` $ <tag> @user [x]"
    escaped = escape_typst(raw)

    assert escaped == r"C\# \* \_ \` \$ \<tag\> \@user \[x\]"


def test_escape_typst_escapes_backslash_first_to_avoid_double_escaping():
    assert escape_typst("a\\b") == r"a\\b"


def test_escape_typst_collapses_newlines():
    assert "\n" not in escape_typst("line one\nline two\r\nline three")
    assert "\r" not in escape_typst("line one\nline two\r\nline three")


def test_build_resume_typst_includes_all_populated_sections():
    source = build_resume_typst(_output(), CONTACT, education=[], certifications=[])

    assert "Jane Doe" in source
    assert "jane\\@example.com" in source
    assert "== Summary" in source
    assert "== Skills" in source
    assert "== Experience" in source
    assert "Backend Engineer" in source
    assert "== Projects" in source
    assert "Side Project" in source


def test_build_resume_typst_omits_empty_sections():
    output = _output(skills=[], projects=[])
    source = build_resume_typst(output, CONTACT, education=[], certifications=[])

    assert "== Skills" not in source
    assert "== Projects" not in source
    assert "== Education" not in source
    assert "== Certifications" not in source


def test_build_resume_typst_includes_education_and_certifications_passthrough():
    education = [{"school": "MIT", "degree": "BSc", "field": "CS", "start_date": dt.date(2016, 9, 1), "end_date": dt.date(2020, 6, 1)}]
    certifications = [{"name": "AWS Cert", "issuer": "Amazon", "date_earned": dt.date(2021, 1, 1)}]

    source = build_resume_typst(_output(), CONTACT, education, certifications)

    assert "== Education" in source
    assert "MIT" in source
    assert "== Certifications" in source
    assert "AWS Cert" in source


def test_build_resume_typst_escapes_user_controlled_bullet_content():
    output = _output()
    output.experience[0].bullets = ["Injected #show: it => [pwned] attempt"]

    source = build_resume_typst(output, CONTACT, education=[], certifications=[])

    # Escaping must precede every "#", never leave one unescaped for Typst
    # to interpret as code.
    assert "\\#show" in source
    assert "\n#show" not in source
    assert " #show" not in source
