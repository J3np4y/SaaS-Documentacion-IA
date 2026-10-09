"""Load local environment configuration without overriding process settings."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

# The project-level .env is ignored by Git and is used for local development.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {
    "1",
    "true",
    "yes",
}
DOCUMENT_STORAGE_DIR = Path(
    os.getenv(
        "DOCUMENT_STORAGE_DIR",
        str(Path(__file__).resolve().parents[3] / ".data" / "documents"),
    )
).expanduser()


def _postgres_url(database: str, port: int) -> str | None:
    """Build a safely escaped PostgreSQL URL from existing Compose settings."""
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        return None
    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", "docs_assistant"),
        password=password,
        host="127.0.0.1",
        port=port,
        database=database,
    ).render_as_string(hide_password=False)


# Explicit URLs supplied by CI or the shell take precedence over local defaults.
os.environ.setdefault(
    "DATABASE_URL",
    _postgres_url(os.getenv("POSTGRES_DB", "docs_assistant"), 5432) or "",
)
os.environ.setdefault(
    "TEST_DATABASE_URL",
    _postgres_url("docs_assistant_test", 5433) or "",
)
