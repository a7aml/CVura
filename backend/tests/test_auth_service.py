import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from app.core.config import settings
from app.core.security import create_refresh_token, hash_password
from app.services import auth_service


class FakeUser:
    def __init__(self, id=None, email="a@example.com", password_hash=None, google_sub=None):
        self.id = id or uuid.uuid4()
        self.email = email
        self.password_hash = password_hash
        self.google_sub = google_sub


class FakeToken:
    def __init__(self, user_id, used_at=None, revoked_at=None, expires_at=None):
        self.user_id = user_id
        self.used_at = used_at
        self.revoked_at = revoked_at
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(days=1)


@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_signup_local_success(mock_user_repo, mock_token_repo):
    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    created = FakeUser()
    mock_user_repo.create_local_user = AsyncMock(return_value=created)
    mock_token_repo.create = AsyncMock()

    user, access_token, refresh_token = await auth_service.signup_local(None, "a@example.com", "password123")

    assert user is created
    assert access_token and refresh_token
    mock_token_repo.create.assert_awaited_once()


@patch("app.services.auth_service.user_repo")
async def test_signup_local_duplicate_email(mock_user_repo):
    mock_user_repo.get_by_email = AsyncMock(return_value=FakeUser())

    with pytest.raises(auth_service.EmailAlreadyExists):
        await auth_service.signup_local(None, "a@example.com", "password123")


@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_login_local_success(mock_user_repo, mock_token_repo):
    existing = FakeUser(password_hash=hash_password("password123"))
    mock_user_repo.get_by_email = AsyncMock(return_value=existing)
    mock_token_repo.create = AsyncMock()

    user, _, _ = await auth_service.login_local(None, existing.email, "password123")
    assert user is existing


@patch("app.services.auth_service.user_repo")
async def test_login_local_wrong_password(mock_user_repo):
    existing = FakeUser(password_hash=hash_password("password123"))
    mock_user_repo.get_by_email = AsyncMock(return_value=existing)

    with pytest.raises(auth_service.InvalidCredentials):
        await auth_service.login_local(None, existing.email, "wrong-password")


@patch("app.services.auth_service.user_repo")
async def test_login_local_unknown_email(mock_user_repo):
    mock_user_repo.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(auth_service.InvalidCredentials):
        await auth_service.login_local(None, "nobody@example.com", "whatever")


@patch("app.services.auth_service.verify_google_id_token")
@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_login_google_creates_new_user(mock_user_repo, mock_token_repo, mock_verify):
    mock_verify.return_value = {"sub": "google-sub-1", "email": "new@example.com"}
    mock_user_repo.get_by_google_sub = AsyncMock(return_value=None)
    mock_user_repo.get_by_email = AsyncMock(return_value=None)
    created = FakeUser(email="new@example.com", google_sub="google-sub-1")
    mock_user_repo.create_google_user = AsyncMock(return_value=created)
    mock_token_repo.create = AsyncMock()

    user, _, _ = await auth_service.login_google(None, "fake-id-token")

    assert user is created
    mock_user_repo.create_google_user.assert_awaited_once_with(None, "new@example.com", "google-sub-1")


@patch("app.services.auth_service.verify_google_id_token")
@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_login_google_existing_user(mock_user_repo, mock_token_repo, mock_verify):
    mock_verify.return_value = {"sub": "google-sub-1", "email": "existing@example.com"}
    existing = FakeUser(email="existing@example.com", google_sub="google-sub-1")
    mock_user_repo.get_by_google_sub = AsyncMock(return_value=existing)
    mock_token_repo.create = AsyncMock()

    user, _, _ = await auth_service.login_google(None, "fake-id-token")
    assert user is existing


@patch("app.services.auth_service.verify_google_id_token")
@patch("app.services.auth_service.user_repo")
async def test_login_google_conflicts_with_local_account(mock_user_repo, mock_verify):
    mock_verify.return_value = {"sub": "google-sub-1", "email": "local@example.com"}
    mock_user_repo.get_by_google_sub = AsyncMock(return_value=None)
    mock_user_repo.get_by_email = AsyncMock(
        return_value=FakeUser(email="local@example.com", password_hash="x")
    )

    with pytest.raises(auth_service.GoogleAccountConflict):
        await auth_service.login_google(None, "fake-id-token")


@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_refresh_rotates_token(mock_user_repo, mock_token_repo):
    user = FakeUser()
    refresh_token = create_refresh_token(user.id)
    stored = FakeToken(user_id=user.id)

    mock_token_repo.get_by_hash = AsyncMock(return_value=stored)
    mock_token_repo.consume = AsyncMock(return_value=stored)
    mock_token_repo.create = AsyncMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=user)

    returned_user, access_token, new_refresh_token = await auth_service.refresh_access_token(
        None, refresh_token
    )

    assert returned_user is user
    assert new_refresh_token != refresh_token
    mock_token_repo.consume.assert_awaited_once()


@patch("app.services.auth_service.refresh_token_repo")
async def test_refresh_reuse_detected_revokes_family(mock_token_repo):
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(user_id)
    stored = FakeToken(user_id=user_id, used_at=datetime.now(timezone.utc))

    mock_token_repo.get_by_hash = AsyncMock(return_value=stored)
    mock_token_repo.consume = AsyncMock(return_value=None)
    mock_token_repo.revoke_all_for_user = AsyncMock()

    with pytest.raises(auth_service.InvalidRefreshToken):
        await auth_service.refresh_access_token(None, refresh_token)

    mock_token_repo.revoke_all_for_user.assert_awaited_once_with(None, user_id)


@patch("app.services.auth_service.refresh_token_repo")
@patch("app.services.auth_service.user_repo")
async def test_refresh_concurrent_replay_loses_race_and_revokes_family(mock_user_repo, mock_token_repo):
    # Simulates two concurrent /auth/refresh requests presenting the same
    # token: both pass the initial read-only checks, but only one `consume`
    # call can win the atomic UPDATE — the other must observe None and
    # trigger family revocation instead of silently minting a second token
    # pair from a single-use token.
    user = FakeUser()
    refresh_token = create_refresh_token(user.id)
    stored = FakeToken(user_id=user.id)

    mock_token_repo.get_by_hash = AsyncMock(return_value=stored)
    mock_token_repo.consume = AsyncMock(side_effect=[stored, None])
    mock_token_repo.create = AsyncMock()
    mock_token_repo.revoke_all_for_user = AsyncMock()
    mock_user_repo.get_by_id = AsyncMock(return_value=user)

    winner = await auth_service.refresh_access_token(None, refresh_token)
    assert winner[0] is user

    with pytest.raises(auth_service.InvalidRefreshToken):
        await auth_service.refresh_access_token(None, refresh_token)

    mock_token_repo.revoke_all_for_user.assert_awaited_once_with(None, user.id)
    assert mock_token_repo.consume.await_count == 2


@patch("app.services.auth_service.refresh_token_repo")
async def test_refresh_expired_token_rejected(mock_token_repo):
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(user_id)
    stored = FakeToken(user_id=user_id, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))

    mock_token_repo.get_by_hash = AsyncMock(return_value=stored)

    with pytest.raises(auth_service.InvalidRefreshToken):
        await auth_service.refresh_access_token(None, refresh_token)


async def test_refresh_rejects_access_token():
    access_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(auth_service.InvalidRefreshToken):
        await auth_service.refresh_access_token(None, access_token)


@patch("app.services.auth_service.refresh_token_repo")
async def test_logout_revokes_token(mock_token_repo):
    stored = FakeToken(user_id=uuid.uuid4())
    mock_token_repo.get_by_hash = AsyncMock(return_value=stored)
    mock_token_repo.revoke = AsyncMock()

    await auth_service.logout(None, "some-refresh-token")

    mock_token_repo.revoke.assert_awaited_once_with(None, stored)
