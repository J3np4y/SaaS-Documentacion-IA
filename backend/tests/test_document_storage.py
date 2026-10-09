"""Unit tests for file validation and private storage keys."""

import asyncio
from io import BytesIO
from unittest.mock import AsyncMock
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from starlette.requests import Request

from app.main import limit_document_upload_request
from app.services.document_storage import (
    MAX_UPLOAD_REQUEST_BYTES,
    InvalidDocument,
    clean_filename,
    object_path,
    validate_document,
)


def test_filename_is_reduced_to_safe_basename() -> None:
    assert clean_filename(r"..\equipo\manual.txt") == "manual.txt"
    assert clean_filename("  informe\u0000.txt  ") == "informe.txt"


@pytest.mark.parametrize(
    ("filename", "content", "expected_type"),
    [
        ("manual.pdf", b"%PDF-1.7\ncontent", "application/pdf"),
        ("manual.txt", "Texto con ñ".encode(), "text/plain"),
    ],
)
def test_validates_supported_file_content(filename, content, expected_type) -> None:
    safe_name, content_type = validate_document(filename, content)
    assert safe_name == filename
    assert content_type == expected_type


def test_validates_docx_archive_structure() -> None:
    result = BytesIO()
    with ZipFile(result, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    assert validate_document("manual.docx", result.getvalue()) == (
        "manual.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("", b"content"),
        ("manual.exe", b"content"),
        ("manual.pdf", b"not a PDF"),
        ("manual.docx", b"not a ZIP"),
        ("manual.txt", b"\xff"),
    ],
)
def test_rejects_unsupported_or_mismatched_file(filename, content) -> None:
    with pytest.raises(InvalidDocument):
        validate_document(filename, content)


def test_storage_key_cannot_escape_private_directory(tmp_path, monkeypatch) -> None:
    from app.services import document_storage

    monkeypatch.setattr(document_storage, "DOCUMENT_STORAGE_DIR", tmp_path / "private")
    with pytest.raises(ValueError):
        object_path("../outside")
    assert not (tmp_path / "outside").exists()


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ([(b"content-length", str(MAX_UPLOAD_REQUEST_BYTES + 1).encode())], 413),
        ([], 411),
    ],
)
def test_upload_middleware_rejects_unbounded_or_oversized_request(
    headers, expected_status
) -> None:
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/organizations/me/documents",
            "headers": headers,
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 1234),
            "http_version": "1.1",
            "query_string": b"",
        }
    )
    call_next = AsyncMock()
    response = asyncio.run(limit_document_upload_request(request, call_next))
    assert response.status_code == expected_status
    call_next.assert_not_awaited()
