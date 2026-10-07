"""Unit tests for password and opaque bearer-secret handling."""

from fastapi import Response
from fastapi.testclient import TestClient

import app.api.auth as auth_api
from app.core.security import hash_password, hash_secret, new_secret, verify_password
from app.main import app

client = TestClient(app)


def test_password_hash_is_salted_and_verifies_only_the_original() -> None:
    first_hash = hash_password("correct-horse-battery-staple")
    second_hash = hash_password("correct-horse-battery-staple")

    assert first_hash.startswith("$argon2id$")
    assert first_hash != second_hash
    assert verify_password("correct-horse-battery-staple", first_hash)
    assert not verify_password("incorrect-password", first_hash)


def test_generated_secret_is_random_and_only_its_hash_is_persisted() -> None:
    first_secret = new_secret()
    second_secret = new_secret()

    assert first_secret != second_secret
    assert len(first_secret) >= 40
    assert hash_secret(first_secret) != first_secret
    assert hash_secret(first_secret) == hash_secret(first_secret)


def test_invalid_auth_request_does_not_echo_password() -> None:
    response = client.post(
        "/auth/register",
        headers={"origin": "http://localhost:3000"},
        json={
            "email": "person@example.com",
            "full_name": "Persona",
            "password": "unsafe",
            "organization_name": "Equipo",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Solicitud no válida"}
    assert "unsafe" not in response.text


def test_session_cookie_is_http_only_secure_and_same_site(monkeypatch) -> None:
    monkeypatch.setattr(auth_api, "SESSION_COOKIE_SECURE", True)
    response = Response()

    auth_api._set_session_cookie(response, "opaque-session-secret")

    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=604800" in cookie
    assert response.headers["cache-control"] == "no-store"
