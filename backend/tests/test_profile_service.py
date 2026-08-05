import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.profile import ProfileCreate, ProfileUpdate
from app.services import profile_service


class FakeProfile:
    def __init__(self, user_id, full_name="Jordan Diaz", summary=None):
        self.id = uuid.uuid4()
        self.user_id = user_id
        self.full_name = full_name
        self.summary = summary


@patch("app.services.profile_service.profile_repo")
async def test_get_full_profile_success(mock_repo):
    user_id = uuid.uuid4()
    existing = FakeProfile(user_id)
    mock_repo.get_by_user_id = AsyncMock(return_value=existing)

    result = await profile_service.get_full_profile(None, user_id)
    assert result is existing


@patch("app.services.profile_service.profile_repo")
async def test_get_full_profile_missing_raises(mock_repo):
    mock_repo.get_by_user_id = AsyncMock(return_value=None)

    with pytest.raises(profile_service.ProfileNotFound):
        await profile_service.get_full_profile(None, uuid.uuid4())


@patch("app.services.profile_service.profile_repo")
async def test_create_profile_success(mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_by_user_id = AsyncMock(return_value=None)
    created = FakeProfile(user_id)
    mock_repo.create_profile = AsyncMock(return_value=created)

    result = await profile_service.create_profile(None, user_id, ProfileCreate(full_name="Jordan Diaz"))
    assert result is created


@patch("app.services.profile_service.profile_repo")
async def test_create_profile_duplicate_raises(mock_repo):
    user_id = uuid.uuid4()
    mock_repo.get_by_user_id = AsyncMock(return_value=FakeProfile(user_id))

    with pytest.raises(profile_service.ProfileAlreadyExists):
        await profile_service.create_profile(None, user_id, ProfileCreate(full_name="Jordan Diaz"))


@patch("app.services.profile_service.profile_repo")
async def test_update_profile_only_sets_provided_fields(mock_repo):
    user_id = uuid.uuid4()
    existing = FakeProfile(user_id)
    mock_repo.get_by_user_id = AsyncMock(return_value=existing)
    mock_repo.update_profile = AsyncMock(return_value=existing)

    await profile_service.update_profile(None, user_id, ProfileUpdate(summary="New summary"))

    mock_repo.update_profile.assert_awaited_once_with(None, existing, commit=True, summary="New summary")


@patch("app.services.profile_service.profile_repo")
async def test_update_profile_missing_raises(mock_repo):
    mock_repo.get_by_user_id = AsyncMock(return_value=None)

    with pytest.raises(profile_service.ProfileNotFound):
        await profile_service.update_profile(None, uuid.uuid4(), ProfileUpdate(summary="x"))
