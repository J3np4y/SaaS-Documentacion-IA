"""Text extraction tests for uploaded document formats."""

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.services.document_processing import (
    DocumentExtractionError,
    extract_document_text,
)


def pdf_with_text(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, value in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode("ascii") + value + b"\nendobj\n")
    xref_offset = len(result)
    result.extend(b"xref\n0 6\n0000000000 65535 f \n")
    result.extend(b"".join(f"{offset:010} 00000 n \n".encode("ascii") for offset in offsets[1:]))
    result.extend(
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(result)


def docx_with_text(text: str) -> bytes:
    result = BytesIO()
    document_xml = (
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    with ZipFile(result, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document_xml)
    return result.getvalue()


@pytest.mark.parametrize(
    ("content_type", "content", "expected_text"),
    [
        ("application/pdf", pdf_with_text("Contrato de vivienda"), "Contrato de vivienda"),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            docx_with_text("Manual de aprendizaje"),
            "Manual de aprendizaje",
        ),
        ("text/plain", "Texto UTF-8: ñ".encode(), "Texto UTF-8: ñ"),
    ],
)
def test_extracts_text_from_supported_formats(content_type, content, expected_text) -> None:
    assert extract_document_text(content_type, content) == expected_text


@pytest.mark.parametrize(
    ("content_type", "content"),
    [
        ("application/pdf", "%PDF-1.7\ncontenido dañado".encode()),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"not a zip"),
        ("text/plain", b"\xff"),
        ("text/plain", b" \n "),
        ("application/unknown", b"content"),
    ],
)
def test_rejects_documents_without_extractable_text(content_type, content) -> None:
    with pytest.raises(DocumentExtractionError):
        extract_document_text(content_type, content)


def test_rejects_extracted_text_over_the_configured_limit() -> None:
    from app.services.document_processing import MAX_EXTRACTED_TEXT_CHARS

    content = b"x" * (MAX_EXTRACTED_TEXT_CHARS + 1)
    with pytest.raises(DocumentExtractionError, match="límite"):
        extract_document_text("text/plain", content)


def test_rejects_pdf_with_too_many_pages(monkeypatch) -> None:
    from app.services import document_processing

    class OversizedPdf:
        pages = [None] * (document_processing.MAX_PDF_PAGES + 1)

    monkeypatch.setattr(document_processing, "PdfReader", lambda *_args, **_kwargs: OversizedPdf())
    with pytest.raises(DocumentExtractionError):
        document_processing.extract_document_text("application/pdf", b"%PDF-1.7")
