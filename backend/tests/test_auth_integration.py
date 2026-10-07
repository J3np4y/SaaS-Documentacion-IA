"""Authentication and authorization checks against isolated PostgreSQL."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.auth import SESSION_COOKIE_NAME
from app.core.database import get_db
from app.core.security import hash_secret
from app.main import app
from app.models import AuthSession, Invitation, Membership, User

ORIGIN = {"origin": "http://localhost:3000"}
PASSWORD = "correct-horse-battery-staple"


@pytest.fixture()
def auth_client(migrated_database):
    def override_get_db():
        with Session(migrated_database) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def register(client: TestClient, email: str, **fields):
    return client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": email,
            "full_name": "Persona de prueba",
            "password": PASSWORD,
            "organization_name": "Organización de prueba",
            **fields,
        },
    )


def test_registration_persists_hashes_and_owner_session(auth_client, migrated_database) -> None:
    response = register(auth_client, "Owner@Example.com")

    assert response.status_code == 201
    assert response.json()["role"] == "owner"
    assert response.json()["email"] == "owner@example.com"
    cookie = response.cookies.get(SESSION_COOKIE_NAME)
    assert cookie
    assert SESSION_COOKIE_NAME not in response.text
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "samesite=lax" in response.headers["set-cookie"].lower()
    assert response.headers["cache-control"] == "no-store"

    with Session(migrated_database) as session:
        user = session.scalar(select(User).where(User.email == "owner@example.com"))
        stored_session = session.scalar(
            select(AuthSession).where(AuthSession.token_hash == hash_secret(cookie))
        )
        membership = session.scalar(select(Membership).where(Membership.user_id == user.id))
        assert user.password_hash != PASSWORD
        assert stored_session is not None
        assert stored_session.token_hash != cookie
        assert membership.role == "owner"

    assert auth_client.get("/auth/me").json()["organization_id"] == response.json()[
        "organization_id"
    ]


def test_login_errors_are_indistinguishable_and_origin_is_required(auth_client) -> None:
    register(auth_client, "known@example.com")
    known = auth_client.post(
        "/auth/login",
        headers=ORIGIN,
        json={"email": "known@example.com", "password": "wrong-password"},
    )
    unknown = auth_client.post(
        "/auth/login",
        headers=ORIGIN,
        json={"email": "unknown@example.com", "password": "wrong-password"},
    )
    no_origin = auth_client.post(
        "/auth/login",
        json={"email": "known@example.com", "password": PASSWORD},
    )

    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()
    assert no_origin.status_code == 403


def test_registration_rejects_short_password_and_duplicate_email(auth_client) -> None:
    short_password = auth_client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": "short@example.com",
            "full_name": "Short",
            "password": "tiny",
            "organization_name": "Example",
        },
    )
    register(auth_client, "duplicate@example.com")
    duplicate = register(auth_client, "duplicate@example.com")

    assert short_password.status_code == 422
    assert "tiny" not in short_password.text
    assert duplicate.status_code == 409


def test_invitation_is_single_use_and_member_cannot_manage_members(auth_client) -> None:
    owner_response = register(auth_client, "owner@example.com")
    invitation = auth_client.post(
        "/organizations/me/invitations", headers=ORIGIN
    )
    member_client = TestClient(app)
    member_response = register(
        member_client,
        "member@example.com",
        organization_name=None,
        invitation_code=invitation.json()["code"],
    )
    reused = register(
        TestClient(app),
        "second-member@example.com",
        organization_name=None,
        invitation_code=invitation.json()["code"],
    )

    assert owner_response.status_code == 201
    assert invitation.status_code == 201
    assert "code" in invitation.json()
    assert member_response.status_code == 201
    assert member_response.json()["role"] == "member"
    assert member_response.json()["organization_id"] == owner_response.json()["organization_id"]
    assert reused.status_code == 400
    assert member_client.get("/organizations/me/members").status_code == 403
    assert len(auth_client.get("/organizations/me/members").json()) == 2


def test_invitation_expiry_is_enforced(auth_client, migrated_database) -> None:
    register(auth_client, "owner@example.com")
    invitation = auth_client.post("/organizations/me/invitations", headers=ORIGIN)
    with Session(migrated_database) as session:
        session.execute(
            update(Invitation)
            .where(Invitation.token_hash == hash_secret(invitation.json()["code"]))
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        session.commit()

    response = register(
        TestClient(app),
        "late@example.com",
        organization_name=None,
        invitation_code=invitation.json()["code"],
    )
    assert response.status_code == 400


def test_invitation_cannot_be_consumed_concurrently(auth_client) -> None:
    register(auth_client, "owner@example.com")
    invitation = auth_client.post("/organizations/me/invitations", headers=ORIGIN)
    code = invitation.json()["code"]

    def accept(email: str):
        with TestClient(app) as client:
            return register(
                client,
                email,
                organization_name=None,
                invitation_code=code,
            )

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(accept, ["one@example.com", "two@example.com"])
        )

    assert sorted(response.status_code for response in responses) == [201, 400]


def test_owner_cannot_remove_last_owner_and_cannot_access_other_tenant(auth_client) -> None:
    first = register(auth_client, "first-owner@example.com")
    last_owner_demotion = auth_client.patch(
        f"/organizations/me/members/{first.json()['id']}",
        headers=ORIGIN,
        json={"role": "member"},
    )
    last_owner_removal = auth_client.delete(
        f"/organizations/me/members/{first.json()['id']}", headers=ORIGIN
    )

    other_client = TestClient(app)
    other = register(other_client, "other-owner@example.com")
    cross_tenant = auth_client.patch(
        f"/organizations/me/members/{other.json()['id']}",
        headers=ORIGIN,
        json={"role": "member"},
    )

    assert last_owner_demotion.status_code == 409
    assert last_owner_removal.status_code == 409
    assert cross_tenant.status_code == 404
    assert len(auth_client.get("/organizations/me/members").json()) == 1
    assert len(other_client.get("/organizations/me/members").json()) == 1


def test_owner_can_manage_roles_and_removal_revokes_member_access(auth_client) -> None:
    owner = register(auth_client, "owner@example.com")
    invitation = auth_client.post("/organizations/me/invitations", headers=ORIGIN)
    member_client = TestClient(app)
    member = register(
        member_client,
        "member@example.com",
        organization_name=None,
        invitation_code=invitation.json()["code"],
    )

    promote = auth_client.patch(
        f"/organizations/me/members/{member.json()['id']}",
        headers=ORIGIN,
        json={"role": "owner"},
    )
    demote = member_client.patch(
        f"/organizations/me/members/{owner.json()['id']}",
        headers=ORIGIN,
        json={"role": "member"},
    )
    remove = member_client.delete(
        f"/organizations/me/members/{owner.json()['id']}", headers=ORIGIN
    )

    assert promote.status_code == 200
    assert promote.json()["role"] == "owner"
    assert demote.status_code == 200
    assert demote.json()["role"] == "member"
    assert remove.status_code == 204
    assert auth_client.get("/auth/me").status_code == 401
    assert member_client.get("/auth/me").status_code == 200


def test_logout_and_expired_session_revoke_access(auth_client, migrated_database) -> None:
    register(auth_client, "session@example.com")
    cookie = auth_client.cookies.get(SESSION_COOKIE_NAME)
    assert auth_client.get("/auth/me").status_code == 200
    with Session(migrated_database) as session:
        session.execute(
            update(AuthSession)
            .where(AuthSession.token_hash == hash_secret(cookie))
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        session.commit()
    assert auth_client.get("/auth/me").status_code == 401

    login = auth_client.post(
        "/auth/login",
        headers=ORIGIN,
        json={"email": "session@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    assert auth_client.post("/auth/logout", headers=ORIGIN).status_code == 204
    assert auth_client.get("/auth/me").status_code == 401
