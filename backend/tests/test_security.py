import uuid
from types import SimpleNamespace

from app.core.security import create_access_token, user_id_key


def _make_request(cookies: dict | None = None, host: str = "1.2.3.4"):
    return SimpleNamespace(cookies=cookies or {}, client=SimpleNamespace(host=host), headers={})


def test_user_id_key_keys_by_user_regardless_of_ip():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)

    request_from_ip_a = _make_request(cookies={"access_token": token}, host="1.2.3.4")
    request_from_ip_b = _make_request(cookies={"access_token": token}, host="9.8.7.6")

    key_a = user_id_key(request_from_ip_a)
    key_b = user_id_key(request_from_ip_b)

    assert key_a == key_b == f"user:{user_id}"


def test_user_id_key_falls_back_to_ip_when_no_cookie():
    request = _make_request(cookies={}, host="1.2.3.4")

    assert user_id_key(request) == "1.2.3.4"


def test_user_id_key_falls_back_to_ip_when_token_invalid():
    request = _make_request(cookies={"access_token": "not-a-real-token"}, host="1.2.3.4")

    assert user_id_key(request) == "1.2.3.4"
