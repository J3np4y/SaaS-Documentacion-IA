"""Document upload and tenant authorization checks against isolated PostgreSQL."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.services import document_storage

ORIGIN = {"origin": "http://localhost:3000"}
PASSWORD = "correct-horse-battery-staple"


@pytest.fixture()
def document_client(migrated_database, tmp_path, monkeypatch):
    monkeypatch.setattr(document_storage, "DOCUMENT_STORAGE_DIR", tmp_path / "private-documents")

    def override_get_db():
        with Session(migrated_database) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": email,
            "full_name": "Persona de prueba",
            "password": PASSWORD,
            "organization_name": "Organización de prueba",
        },
    )
    assert response.status_code == 201
    return response.json()


def docx_content() -> bytes:
    result = BytesIO()
    with ZipFile(result, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return result.getvalue()


def test_upload_list_download_and_permanently_delete_document(document_client) -> None:
    register(document_client, "owner@example.com")
    content = b"Documento de aprendizaje\n"
    uploaded = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("../manual.txt", content, "application/octet-stream")},
    )

    assert uploaded.status_code == 201
    document = uploaded.json()
    assert document["filename"] == "manual.txt"
    assert document["content_type"] == "text/plain"
    assert document["size_bytes"] == len(content)
    assert uploaded.headers["cache-control"] == "no-store"
    assert len(list((document_storage.DOCUMENT_STORAGE_DIR).iterdir())) == 1

    listing = document_client.get("/organizations/me/documents")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()] == [document["id"]]
    assert listing.headers["cache-control"] == "no-store"

    download = document_client.get(
        f"/organizations/me/documents/{document['id']}/download"
    )
    assert download.content == content
    assert download.headers["content-type"] == "text/plain; charset=utf-8"
    assert download.headers["content-disposition"].startswith("attachment;")
    assert download.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in download.headers["content-security-policy"]

    deleted = document_client.delete(
        f"/organizations/me/documents/{document['id']}", headers=ORIGIN
    )
    assert deleted.status_code == 204
    assert document_client.get("/organizations/me/documents").json() == []
    assert list(document_storage.DOCUMENT_STORAGE_DIR.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("manual.pdf", b"%PDF-1.7\ncontent"),
        ("manual.docx", docx_content()),
        ("manual.txt", "Texto UTF-8: ñ".encode()),
    ],
)
def test_upload_accepts_the_agreed_file_types(document_client, filename, content) -> None:
    register(document_client, f"{filename.replace('.', '-')}@example.com")
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == 201
    assert response.json()["filename"] == filename


def test_upload_accepts_a_file_at_the_exact_size_limit(document_client) -> None:
    register(document_client, "limit@example.com")
    content = b"x" * (10 * 1024 * 1024)
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("limit.txt", content, "text/plain")},
    )

    assert response.status_code == 201
    assert response.json()["size_bytes"] == 10 * 1024 * 1024


@pytest.mark.parametrize(
    ("filename", "content_size", "content", "expected_status"),
    [
        ("empty.txt", 0, b"", 400),
        ("fake.txt", 8, b"%PDF-1.7", 400),
        ("fake-archive.txt", 24, b"PK\x03\x04" + b"\x00" * 20, 400),
        ("unknown.exe", 8, b"anything", 400),
        ("large.txt", 10 * 1024 * 1024 + 1, None, 413),
    ],
)
def test_upload_rejects_invalid_or_oversized_files(
    document_client, filename, content_size, content, expected_status
) -> None:
    register(document_client, f"{filename.replace('.', '-')}@example.com")
    if content is None:
        content = b"a" * content_size
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == expected_status
    assert document_client.get("/organizations/me/documents").json() == []
    assert not document_storage.DOCUMENT_STORAGE_DIR.exists()


def test_documents_are_scoped_to_membership_and_organization(document_client) -> None:
    owner = register(document_client, "owner@example.com")
    invitation = document_client.post("/organizations/me/invitations", headers=ORIGIN)
    member_client = TestClient(app)
    member = member_client.post(
        "/auth/register",
        headers=ORIGIN,
        json={
            "email": "member@example.com",
            "full_name": "Integrante",
            "password": PASSWORD,
            "invitation_code": invitation.json()["code"],
        },
    )
    assert member.status_code == 201
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("shared.txt", b"visible in the organization", "text/plain")},
    )
    document_id = upload.json()["id"]

    other_client = TestClient(app)
    other = register(other_client, "other@example.com")

    assert member_client.get("/organizations/me/documents").json()[0]["id"] == document_id
    assert member_client.get(
        f"/organizations/me/documents/{document_id}/download"
    ).content == b"visible in the organization"
    assert member_client.delete(
        f"/organizations/me/documents/{document_id}", headers=ORIGIN
    ).status_code == 204
    assert document_client.get("/organizations/me/documents").json() == []
    assert other["organization_id"] != owner["organization_id"]
    assert other_client.get("/organizations/me/documents").json() == []
    assert other_client.get(
        f"/organizations/me/documents/{document_id}/download"
    ).status_code == 404
    assert other_client.delete(
        f"/organizations/me/documents/{document_id}", headers=ORIGIN
    ).status_code == 404


def test_document_writes_require_authentication_and_same_origin(document_client) -> None:
    unauthenticated = document_client.get("/organizations/me/documents")
    assert unauthenticated.status_code == 401

    register(document_client, "owner@example.com")
    no_origin = document_client.post(
        "/organizations/me/documents",
        files={"file": ("manual.txt", b"content", "text/plain")},
    )
    assert no_origin.status_code == 403
    assert document_client.get("/organizations/me/documents").json() == []


def test_upload_cleans_private_file_when_database_commit_fails(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")

    def fail_commit(_session):
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"content", "text/plain")},
    )

    assert response.status_code == 500
    assert document_client.get("/organizations/me/documents").json() == []
    assert list(document_storage.DOCUMENT_STORAGE_DIR.iterdir()) == []


def test_delete_restores_file_when_database_commit_fails(
    document_client, monkeypatch
) -> None:
    register(document_client, "owner@example.com")
    upload = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"content", "text/plain")},
    )
    document = upload.json()

    def fail_commit(_session):
        raise SQLAlchemyError("simulated database failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = document_client.delete(
        f"/organizations/me/documents/{document['id']}", headers=ORIGIN
    )

    assert response.status_code == 500
    assert document_client.get("/organizations/me/documents").json()[0]["id"] == document["id"]
    assert len(list(document_storage.DOCUMENT_STORAGE_DIR.iterdir())) == 1


def test_upload_rejects_excessive_multipart_overhead_before_parsing(document_client) -> None:
    register(document_client, "owner@example.com")
    response = document_client.post(
        "/organizations/me/documents",
        headers=ORIGIN,
        files={"file": ("manual.txt", b"x" * (10 * 1024 * 1024), "text/plain")},
        data={"extra": "x" * (64 * 1024 + 1)},
    )

    assert response.status_code == 413
    assert document_client.get("/organizations/me/documents").json() == []
