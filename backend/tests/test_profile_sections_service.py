import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.services import profile_sections_service as sections


class FakeProfile:
    def __init__(self, profile_id=None):
        self.id = profile_id or uuid.uuid4()


class FakeItem:
    def __init__(self, profile_id):
        self.id = uuid.uuid4()
        self.profile_id = profile_id


@patch("app.services.profile_sections_service.education_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_add_education_success(mock_profile_repo, mock_education_repo):
    profile = FakeProfile()
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=profile)
    created = FakeItem(profile.id)
    mock_education_repo.create = AsyncMock(return_value=created)

    result = await sections.add_education(None, uuid.uuid4(), {"school": "Test U"})

    assert result is created
    mock_education_repo.create.assert_awaited_once_with(None, profile.id, school="Test U")


@patch("app.services.profile_sections_service.profile_repo")
async def test_add_education_no_profile_raises(mock_profile_repo):
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=None)

    with pytest.raises(sections.ProfileNotFound):
        await sections.add_education(None, uuid.uuid4(), {"school": "Test U"})


@patch("app.services.profile_sections_service.education_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_update_education_success(mock_profile_repo, mock_education_repo):
    profile = FakeProfile()
    item = FakeItem(profile.id)
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=profile)
    mock_education_repo.get_by_id = AsyncMock(return_value=item)
    mock_education_repo.update = AsyncMock(return_value=item)

    result = await sections.update_education(None, uuid.uuid4(), item.id, {"school": "New U"})
    assert result is item


@patch("app.services.profile_sections_service.education_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_update_education_rejects_item_from_another_profile(mock_profile_repo, mock_education_repo):
    # The core IDOR check: an item belonging to someone else's profile must
    # never be mutated, even if the caller supplies a valid item id.
    my_profile = FakeProfile()
    someone_elses_item = FakeItem(profile_id=uuid.uuid4())
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=my_profile)
    mock_education_repo.get_by_id = AsyncMock(return_value=someone_elses_item)

    with pytest.raises(sections.ItemNotFound):
        await sections.update_education(None, uuid.uuid4(), someone_elses_item.id, {"school": "Hijacked"})


@patch("app.services.profile_sections_service.education_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_delete_education_rejects_item_from_another_profile(mock_profile_repo, mock_education_repo):
    my_profile = FakeProfile()
    someone_elses_item = FakeItem(profile_id=uuid.uuid4())
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=my_profile)
    mock_education_repo.get_by_id = AsyncMock(return_value=someone_elses_item)

    with pytest.raises(sections.ItemNotFound):
        await sections.delete_education(None, uuid.uuid4(), someone_elses_item.id)


@patch("app.services.profile_sections_service.education_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_update_education_missing_item_raises(mock_profile_repo, mock_education_repo):
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=FakeProfile())
    mock_education_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(sections.ItemNotFound):
        await sections.update_education(None, uuid.uuid4(), uuid.uuid4(), {"school": "X"})


@patch("app.services.profile_sections_service.skills_repo")
@patch("app.services.profile_sections_service.profile_repo")
async def test_add_skill_follows_the_same_pattern(mock_profile_repo, mock_skills_repo):
    profile = FakeProfile()
    mock_profile_repo.get_by_user_id = AsyncMock(return_value=profile)
    created = FakeItem(profile.id)
    mock_skills_repo.create = AsyncMock(return_value=created)

    result = await sections.add_skill(None, uuid.uuid4(), {"name": "Python"})
    assert result is created
