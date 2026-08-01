import uuid

from app.repositories import (
    awards_repo,
    certifications_repo,
    education_repo,
    experiences_repo,
    languages_repo,
    profile_repo,
    projects_repo,
    skills_repo,
)


class ProfileNotFound(Exception):
    pass


class ItemNotFound(Exception):
    pass


async def _owned_profile_id(db, user_id: uuid.UUID) -> uuid.UUID:
    profile = await profile_repo.get_by_user_id(db, user_id)
    if profile is None:
        raise ProfileNotFound()
    return profile.id


def _assert_owned(item, profile_id: uuid.UUID) -> None:
    if item is None or item.profile_id != profile_id:
        raise ItemNotFound()


# --- education ---


async def add_education(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await education_repo.create(db, profile_id, **data)


async def update_education(db, user_id: uuid.UUID, education_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await education_repo.get_by_id(db, education_id)
    _assert_owned(item, profile_id)
    return await education_repo.update(db, item, **data)


async def delete_education(db, user_id: uuid.UUID, education_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await education_repo.get_by_id(db, education_id)
    _assert_owned(item, profile_id)
    await education_repo.delete(db, item)


# --- experiences ---


async def add_experience(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await experiences_repo.create(db, profile_id, **data)


async def update_experience(db, user_id: uuid.UUID, experience_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await experiences_repo.get_by_id(db, experience_id)
    _assert_owned(item, profile_id)
    return await experiences_repo.update(db, item, **data)


async def delete_experience(db, user_id: uuid.UUID, experience_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await experiences_repo.get_by_id(db, experience_id)
    _assert_owned(item, profile_id)
    await experiences_repo.delete(db, item)


# --- projects ---


async def add_project(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await projects_repo.create(db, profile_id, **data)


async def update_project(db, user_id: uuid.UUID, project_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await projects_repo.get_by_id(db, project_id)
    _assert_owned(item, profile_id)
    return await projects_repo.update(db, item, **data)


async def delete_project(db, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await projects_repo.get_by_id(db, project_id)
    _assert_owned(item, profile_id)
    await projects_repo.delete(db, item)


# --- skills ---


async def add_skill(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await skills_repo.create(db, profile_id, **data)


async def update_skill(db, user_id: uuid.UUID, skill_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await skills_repo.get_by_id(db, skill_id)
    _assert_owned(item, profile_id)
    return await skills_repo.update(db, item, **data)


async def delete_skill(db, user_id: uuid.UUID, skill_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await skills_repo.get_by_id(db, skill_id)
    _assert_owned(item, profile_id)
    await skills_repo.delete(db, item)


# --- certifications ---


async def add_certification(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await certifications_repo.create(db, profile_id, **data)


async def update_certification(db, user_id: uuid.UUID, certification_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await certifications_repo.get_by_id(db, certification_id)
    _assert_owned(item, profile_id)
    return await certifications_repo.update(db, item, **data)


async def delete_certification(db, user_id: uuid.UUID, certification_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await certifications_repo.get_by_id(db, certification_id)
    _assert_owned(item, profile_id)
    await certifications_repo.delete(db, item)


# --- languages ---


async def add_language(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await languages_repo.create(db, profile_id, **data)


async def update_language(db, user_id: uuid.UUID, language_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await languages_repo.get_by_id(db, language_id)
    _assert_owned(item, profile_id)
    return await languages_repo.update(db, item, **data)


async def delete_language(db, user_id: uuid.UUID, language_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await languages_repo.get_by_id(db, language_id)
    _assert_owned(item, profile_id)
    await languages_repo.delete(db, item)


# --- awards ---


async def add_award(db, user_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    return await awards_repo.create(db, profile_id, **data)


async def update_award(db, user_id: uuid.UUID, award_id: uuid.UUID, data: dict):
    profile_id = await _owned_profile_id(db, user_id)
    item = await awards_repo.get_by_id(db, award_id)
    _assert_owned(item, profile_id)
    return await awards_repo.update(db, item, **data)


async def delete_award(db, user_id: uuid.UUID, award_id: uuid.UUID) -> None:
    profile_id = await _owned_profile_id(db, user_id)
    item = await awards_repo.get_by_id(db, award_id)
    _assert_owned(item, profile_id)
    await awards_repo.delete(db, item)
