from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import PASSWORD, register

API = "/api/v1"


def test_health(client):
    r = client.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["checks"]["database"] == "ok"


def test_register_sets_httponly_cookie_and_defaults(client):
    r = client.post(f"{API}/auth/register",
                    json={"email": "Anna@Example.com", "password": PASSWORD, "display_name": " Anna "})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "anna@example.com"
    assert body["display_name"] == "Anna"
    assert body["preferences"]["target_language"] == "de"
    assert body["preferences"]["explanation_language"] == "en"
    cookie = r.headers["set-cookie"]
    assert "sv_session=" in cookie and "HttpOnly" in cookie
    assert "password" not in r.text


def test_register_creates_default_collections(auth_client):
    names = [c["name"] for c in auth_client.get(f"{API}/collections").json()]
    assert "German A1" in names and "Business German" in names and len(names) == 12


def test_duplicate_email_rejected_case_insensitive(client):
    register(client, "anna@example.com")
    r = client.post(f"{API}/auth/register",
                    json={"email": "ANNA@example.com", "password": PASSWORD, "display_name": "A"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "email_taken"


def test_weak_password_rejected(client):
    r = client.post(f"{API}/auth/register", json={"email": "a@example.com", "password": "short", "display_name": "A"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_login_and_wrong_password(client):
    register(client)
    fresh = TestClient(app)
    assert fresh.post(f"{API}/auth/login", json={"email": "anna@example.com", "password": "wrongpass1"}).status_code == 401
    r = fresh.post(f"{API}/auth/login", json={"email": "anna@example.com", "password": PASSWORD})
    assert r.status_code == 200
    assert fresh.get(f"{API}/users/me").json()["email"] == "anna@example.com"


def test_unknown_email_gives_same_error(client):
    r = client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_requires_auth(client):
    assert client.get(f"{API}/users/me").status_code == 401
    assert client.get(f"{API}/vocabulary").status_code == 401
    assert client.get(f"{API}/analytics/dashboard").status_code == 401


def test_logout_revokes_all_tokens(client):
    register(client)
    token = client.cookies.get("sv_session")
    other = TestClient(app)
    assert other.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.post(f"{API}/auth/logout").status_code == 204
    # The old token no longer works anywhere, even if someone copied it.
    assert other.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_tampered_token_rejected(client):
    assert client.get(f"{API}/users/me", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_update_preferences(auth_client):
    r = auth_client.patch(f"{API}/users/me/preferences",
                          json={"explanation_language": "hi", "cefr_level": "C1", "daily_new_cards": 25, "theme": "dark"})
    assert r.status_code == 200, r.text
    p = r.json()
    assert (p["explanation_language"], p["cefr_level"], p["daily_new_cards"], p["theme"]) == ("hi", "C1", 25, "dark")
    assert auth_client.patch(f"{API}/users/me/preferences", json={"cefr_level": "D1"}).status_code == 422
    assert auth_client.patch(f"{API}/users/me/preferences", json={"explanation_language": "de"}).status_code == 422
    assert auth_client.patch(f"{API}/users/me/preferences", json={"timezone": "Mars/Base"}).status_code == 422


def test_delete_account_removes_data(auth_client):
    auth_client.post(f"{API}/vocabulary", json={"term": "Termin", "part_of_speech": "noun"})
    assert auth_client.delete(f"{API}/users/me").status_code == 204
    r = TestClient(app).post(f"{API}/auth/login", json={"email": "anna@example.com", "password": PASSWORD})
    assert r.status_code == 401


def test_rate_limit_on_login(client, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "auth_rate_limit_per_minute", 3)
    codes = [client.post(f"{API}/auth/login", json={"email": "x@example.com", "password": "nope12345"}).status_code
             for _ in range(5)]
    assert codes[:3] == [401, 401, 401]
    assert 429 in codes[3:]
