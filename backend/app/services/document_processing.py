"""Text extraction for the document formats accepted by the application."""

from io import BytesIO
from xml.etree.ElementTree import ParseError, fromstring
from zipfile import BadZipFile, ZipFile

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_EXTRACTED_TEXT_CHARS = 100_000
MAX_PDF_PAGES = 1_000
WORD_NAMESPACE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class DocumentExtractionError(ValueError):
    """The document is stored but its text could not be extracted safely."""


def _validate_text(text: str) -> str:
    text = text.strip()
    if not text:
        raise DocumentExtractionError("El documento no contiene texto extraíble.")
    if len(text) > MAX_EXTRACTED_TEXT_CHARS:
        raise DocumentExtractionError("El texto extraído supera el límite permitido.")
    return text


def _extract_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content), strict=False)
        if len(reader.pages) > MAX_PDF_PAGES:
            raise DocumentExtractionError("El PDF contiene demasiadas páginas.")
        pages = []
        total_chars = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            total_chars += len(page_text)
            if total_chars > MAX_EXTRACTED_TEXT_CHARS:
                raise DocumentExtractionError("El texto extraído supera el límite permitido.")
            pages.append(page_text)
    except (PdfReadError, OSError, ValueError):
        raise DocumentExtractionError("No se pudo leer el contenido del PDF.") from None
    return _validate_text("\n".join(pages))


def _extract_docx(content: bytes) -> str:
    try:
        with ZipFile(BytesIO(content)) as archive:
            document_xml = archive.read("word/document.xml")
        root = fromstring(document_xml)
    except (BadZipFile, KeyError, OSError, ParseError):
        raise DocumentExtractionError("No se pudo leer el contenido del DOCX.") from None

    paragraphs = []
    total_chars = 0
    for paragraph in root.iter(f"{WORD_NAMESPACE}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{WORD_NAMESPACE}t"))
        if text:
            total_chars += len(text)
            if total_chars > MAX_EXTRACTED_TEXT_CHARS:
                raise DocumentExtractionError("El texto extraído supera el límite permitido.")
            paragraphs.append(text)
    return _validate_text("\n".join(paragraphs))


def extract_document_text(content_type: str, content: bytes) -> str:
    if content_type == "application/pdf":
        return _extract_pdf(content)
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(content)
    if content_type == "text/plain":
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise DocumentExtractionError("No se pudo leer el contenido TXT.") from None
        return _validate_text(text)
    raise DocumentExtractionError("El formato del documento no está admitido.")
