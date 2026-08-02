import uuid
from datetime import date

from app.services import resume_selection_service as selection


def _skill(name, is_core=False):
    return {"name": name, "is_core": is_core}


def _experience(title, company, bullets, start_date=None, end_date=None):
    return {
        "id": uuid.uuid4(),
        "title": title,
        "company": company,
        "bullets": bullets,
        "start_date": start_date,
        "end_date": end_date,
    }


def _project(name, description="", tech_stack=None):
    return {"id": uuid.uuid4(), "name": name, "description": description, "tech_stack": tech_stack or []}


JOB_ANALYSIS = {
    "required_skills": ["Python", "PostgreSQL"],
    "technologies": ["Python", "Docker"],
    "keywords_ats": ["REST API"],
    "preferred_skills": ["Kafka", "GraphQL", "Redis", "Terraform", "Ansible", "gRPC"],
}


def test_normalize_strips_punctuation_and_lowercases():
    assert selection.normalize("  REST-API! ") == "rest api"


def test_alias_matching_js_matches_javascript_requirement():
    weighted = selection.build_jd_keyword_weights({"required_skills": ["JavaScript"]})
    assert selection.normalize("JS") in weighted
    assert weighted[selection.normalize("JS")] == 3


def test_score_skills_includes_all_required_matches_and_capped_preferred_matches():
    profile_skills = [
        _skill("Python"),
        _skill("PostgreSQL"),
        _skill("Docker"),
        _skill("Kafka"),
        _skill("GraphQL"),
        _skill("Redis"),
        _skill("Terraform"),
        _skill("Ansible"),
        _skill("gRPC"),
        _skill("Excel"),
    ]
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_skills(profile_skills, jd_weighted)

    assert "Python" in selected
    assert "PostgreSQL" in selected
    assert "Docker" in selected
    assert "Excel" not in selected
    preferred_selected = [s for s in selected if s in {"Kafka", "GraphQL", "Redis", "Terraform", "Ansible", "gRPC"}]
    assert len(preferred_selected) == selection.MAX_PREFERRED_SKILLS


def test_score_skills_always_includes_core_flagged_skill_even_without_jd_match():
    profile_skills = [_skill("Excel", is_core=True)]
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_skills(profile_skills, jd_weighted)

    assert "Excel" in selected


def test_score_experiences_normal_match_ranks_relevant_role_higher():
    matching = _experience(
        "Backend Engineer",
        "Acme",
        ["Built REST API services in Python", "Managed PostgreSQL databases"],
        date(2022, 1, 1),
        date(2023, 1, 1),
    )
    unrelated = _experience(
        "Barista",
        "Cafe Co",
        ["Made coffee", "Handled cash register"],
        date(2019, 1, 1),
        date(2020, 1, 1),
    )
    current = _experience(
        "Staff Engineer", "Globex", ["Led platform team"], date(2023, 2, 1), None
    )
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_experiences([matching, unrelated, current], jd_weighted)
    ids = [e.experience_id for e in selected]

    assert matching["id"] in ids
    assert current["id"] in ids
    matching_entry = next(e for e in selected if e.experience_id == matching["id"])
    unrelated_entry = next((e for e in selected if e.experience_id == unrelated["id"]), None)
    if unrelated_entry is not None:
        assert matching_entry.score > unrelated_entry.score


def test_score_experiences_recency_force_include_even_with_zero_relevance():
    old_matching = _experience(
        "Backend Engineer",
        "Acme",
        ["Built REST API services in Python"],
        date(2015, 1, 1),
        date(2016, 1, 1),
    )
    current_irrelevant = _experience(
        "Retail Associate", "ShopCo", ["Folded shirts"], date(2023, 1, 1), None
    )
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_experiences([old_matching, current_irrelevant], jd_weighted)
    ids = {e.experience_id for e in selected}

    assert current_irrelevant["id"] in ids


def test_score_experiences_zero_match_falls_back_to_most_recent_n():
    unrelated_old = _experience("Barista", "Cafe Co", ["Made coffee"], date(2018, 1, 1), date(2019, 1, 1))
    unrelated_new = _experience("Cashier", "ShopCo", ["Handled register"], date(2020, 1, 1), date(2021, 1, 1))
    jd_weighted = selection.build_jd_keyword_weights({"required_skills": ["Rust"], "technologies": [], "keywords_ats": [], "preferred_skills": []})

    selected = selection.score_experiences([unrelated_old, unrelated_new], jd_weighted)

    assert len(selected) == 2
    assert selected[0].experience_id == unrelated_new["id"]
    assert all(e.score == 0.0 for e in selected)


def test_score_experiences_empty_profile_returns_empty_list():
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)
    assert selection.score_experiences([], jd_weighted) == []


def test_score_experiences_caps_at_max_experiences():
    experiences = [
        _experience(f"Engineer {i}", "Acme", ["Built REST API in Python"], date(2010 + i, 1, 1), date(2011 + i, 1, 1))
        for i in range(8)
    ]
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_experiences(experiences, jd_weighted)

    assert len(selected) == selection.MAX_EXPERIENCES


def test_score_projects_normal_match_and_cap():
    matching = [
        _project(f"API Project {i}", "Built a REST API in Python with PostgreSQL", ["Python", "PostgreSQL"])
        for i in range(5)
    ]
    jd_weighted = selection.build_jd_keyword_weights(JOB_ANALYSIS)

    selected = selection.score_projects(matching, jd_weighted)

    assert len(selected) == selection.MAX_PROJECTS
    assert all(p.score > 0 for p in selected)


def test_score_projects_zero_match_falls_back_to_profile_order():
    projects = [_project("Painting App", "A hobby art project"), _project("Garden Planner", "For my backyard")]
    jd_weighted = selection.build_jd_keyword_weights({"required_skills": ["Rust"], "technologies": [], "keywords_ats": [], "preferred_skills": []})

    selected = selection.score_projects(projects, jd_weighted)

    assert [p.project_id for p in selected] == [p["id"] for p in projects]
    assert all(p.score == 0.0 for p in selected)


def test_select_resume_content_builds_full_selection():
    profile_skills = [_skill("Python")]
    profile_experiences = [_experience("Backend Engineer", "Acme", ["Built REST API in Python"], date(2022, 1, 1), None)]
    profile_projects = [_project("API Project", "Built a REST API in Python", ["Python"])]

    result = selection.select_resume_content(profile_skills, profile_experiences, profile_projects, JOB_ANALYSIS)

    assert result.selected_skills == ["Python"]
    assert len(result.selected_experiences) == 1
    assert len(result.selected_projects) == 1
