"""Integration checks against a dedicated PostgreSQL test database."""

import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import settings  # noqa: F401  (loads .env and derives local URLs)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
DATABASE_URL = os.getenv("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="Define TEST_DATABASE_URL para las pruebas PostgreSQL"
)


@pytest.fixture()
def migrated_database():
    """Apply migrations to a disposable database before each integration test."""
    assert DATABASE_URL is not None
    # Prevent the destructive schema reset below from targeting development data.
    if make_url(DATABASE_URL).database != "docs_assistant_test":
        pytest.fail("TEST_DATABASE_URL debe apuntar a la base docs_assistant_test")
    environment = os.environ.copy()
    environment["DATABASE_URL"] = DATABASE_URL
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    engine = create_engine(DATABASE_URL)
    try:
        yield engine
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
        engine.dispose()


def test_migration_creates_tables(migrated_database) -> None:
    inspector = inspect(migrated_database)
    assert set(inspector.get_table_names()) >= {"alembic_version", "organizations", "documents"}


def test_document_requires_existing_organization(migrated_database) -> None:
    from app.models import Document

    with Session(migrated_database) as session, pytest.raises(IntegrityError):
        session.add(
            Document(
                organization_id=uuid4(), filename="manual.pdf", content_type="application/pdf"
            )
        )
        session.commit()


def test_organization_and_document_metadata_persist(migrated_database) -> None:
    from app.models import Document, Organization

    with Session(migrated_database) as session:
        organization = Organization(name="Empresa de prueba", slug=f"empresa-{uuid4().hex[:8]}")
        session.add(organization)
        session.flush()
        document = Document(
            organization_id=organization.id,
            filename="manual.pdf",
            content_type="application/pdf",
        )
        session.add(document)
        session.commit()

        stored = session.get(Document, document.id)
        assert stored is not None
        assert stored.organization_id == organization.id
