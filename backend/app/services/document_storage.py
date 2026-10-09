"""Private local storage and basic validation for uploaded documents."""

import os
import re
import unicodedata
import zipfile
from io import BytesIO
from pathlib import Path

from app.core.settings import DOCUMENT_STORAGE_DIR

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_REQUEST_BYTES = MAX_DOCUMENT_SIZE_BYTES + 64 * 1024
MAX_DOCX_UNCOMPRESSED_SIZE = 50 * 1024 * 1024
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}
STORAGE_KEY_PATTERN = re.compile(r"^[a-f0-9]{32}$")


class InvalidDocument(ValueError):
    """The uploaded filename or content is not an accepted document."""


def clean_filename(filename: str | None) -> str:
    if not filename:
        raise InvalidDocument("El archivo debe tener un nombre.")
    basename = filename.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    safe_name = "".join(
        character for character in basename
        if not unicodedata.category(character).startswith("C")
    ).strip().strip(".")
    if not safe_name:
        raise InvalidDocument("El nombre del archivo no es válido.")
    if len(safe_name) > 255:
        suffix = Path(safe_name).suffix[:20]
        safe_name = f"{safe_name[:255 - len(suffix)]}{suffix}"
    return safe_name


def validate_document(filename: str | None, content: bytes) -> tuple[str, str]:
    safe_name = clean_filename(filename)
    suffix = Path(safe_name).suffix.lower()
    content_type = CONTENT_TYPES.get(suffix)
    if content_type is None:
        raise InvalidDocument("Solo se aceptan archivos PDF, DOCX y TXT.")
    if not content:
        raise InvalidDocument("El archivo está vacío.")

    if suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise InvalidDocument("El contenido no parece ser un documento PDF.")
    elif suffix == ".docx":
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                entries = {entry.filename: entry for entry in archive.infolist()}
                if len(entries) > 4096:
                    raise InvalidDocument("El documento DOCX contiene demasiados elementos.")
                required_entries = {"[Content_Types].xml", "word/document.xml"}
                if not required_entries.issubset(entries):
                    raise InvalidDocument("El contenido no parece ser un documento DOCX.")
                if sum(entry.file_size for entry in entries.values()) > MAX_DOCX_UNCOMPRESSED_SIZE:
                    raise InvalidDocument("El documento DOCX excede el tamaño expandido permitido.")
        except (OSError, zipfile.BadZipFile):
            raise InvalidDocument("El contenido no parece ser un documento DOCX.") from None
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise InvalidDocument("Los archivos TXT deben usar codificación UTF-8.") from None
        if "\x00" in text:
            raise InvalidDocument("El archivo TXT contiene datos no válidos.")

    return safe_name, content_type


def _storage_root() -> Path:
    root = DOCUMENT_STORAGE_DIR.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        root.chmod(0o700)
    return root


def object_path(storage_key: str) -> Path:
    if not STORAGE_KEY_PATTERN.fullmatch(storage_key):
        raise ValueError("Clave de almacenamiento no válida")
    root = _storage_root()
    path = (root / storage_key).resolve()
    if path.parent != root:
        raise ValueError("Clave de almacenamiento fuera del directorio permitido")
    return path


def store_object(storage_key: str, content: bytes) -> None:
    path = object_path(storage_key)
    created = False
    try:
        with path.open("xb") as stored_file:
            created = True
            stored_file.write(content)
        if os.name == "posix":
            path.chmod(0o600)
    except OSError:
        if created:
            path.unlink(missing_ok=True)
        raise


def read_object(storage_key: str) -> bytes:
    return object_path(storage_key).read_bytes()


def delete_object(storage_key: str) -> None:
    object_path(storage_key).unlink()
