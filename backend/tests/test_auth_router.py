"""Router-level rate-limit coverage for /auth: the brute-force-sensitive
endpoints (signup, login, google) each declare @limiter.limit("5/minute")
in app/routers/auth.py, but that had no HTTP-level test verifying the
decorator actually engages — these close that gap."""

import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.core.security import limiter
from app.main import app
from app.models.user import User

FAKE_USER = User(id=uuid.uuid4(), email="jane@example.com", plan="free")


def _client():
    limiter.reset()
    return TestClient(app)


@patch("app.routers.auth.auth_service.signup_local", new_callable=AsyncMock)
def test_signup_rate_limited_after_five_requests_per_minute(mock_signup):
    mock_signup.return_value = (FAKE_USER, "access", "refresh")
    client = _client()

    responses = [
        client.post("/auth/signup", json={"email": f"u{i}@example.com", "password": "hunter22"})
        for i in range(6)
    ]

    assert [r.status_code for r in responses[:5]] == [200] * 5
    assert responses[5].status_code == 429


@patch("app.routers.auth.auth_service.login_local", new_callable=AsyncMock)
def test_login_rate_limited_after_five_requests_per_minute(mock_login):
    mock_login.return_value = (FAKE_USER, "access", "refresh")
    client = _client()

    responses = [
        client.post("/auth/login", json={"email": "jane@example.com", "password": "hunter22"}) for _ in range(6)
    ]

    assert [r.status_code for r in responses[:5]] == [200] * 5
    assert responses[5].status_code == 429


@patch("app.routers.auth.auth_service.login_google", new_callable=AsyncMock)
def test_google_login_rate_limited_after_five_requests_per_minute(mock_login_google):
    mock_login_google.return_value = (FAKE_USER, "access", "refresh")
    client = _client()

    responses = [client.post("/auth/google", json={"id_token": "fake-token"}) for _ in range(6)]

    assert [r.status_code for r in responses[:5]] == [200] * 5
    assert responses[5].status_code == 429
