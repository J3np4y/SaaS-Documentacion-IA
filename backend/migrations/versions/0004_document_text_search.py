"""Store extracted document text and index it for Spanish full-text search."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_document_text_search"
down_revision: str | None = "0003_document_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "extraction_status",
            sa.String(length=16),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('spanish'::regconfig, coalesce(extracted_text, ''::text))",
                persisted=True,
            ),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_documents_extraction_status",
        "documents",
        "extraction_status IN ('pending', 'ready', 'failed')",
    )
    op.create_index(
        "ix_documents_search_vector",
        "documents",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_documents_search_vector", table_name="documents")
    op.drop_constraint("ck_documents_extraction_status", "documents", type_="check")
    op.drop_column("documents", "search_vector")
    op.drop_column("documents", "extraction_status")
    op.drop_column("documents", "extracted_text")
