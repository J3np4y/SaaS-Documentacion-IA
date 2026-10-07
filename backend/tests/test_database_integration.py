"""Integration checks against a dedicated PostgreSQL test database."""

from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


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
