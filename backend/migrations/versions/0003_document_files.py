"""Add private file references and sizes to document metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_document_files"
down_revision: str | None = "0002_authentication"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("storage_key", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("size_bytes", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.create_unique_constraint("uq_documents_storage_key", "documents", ["storage_key"])


def downgrade() -> None:
    op.drop_constraint("uq_documents_storage_key", "documents", type_="unique")
    op.drop_column("documents", "size_bytes")
    op.drop_column("documents", "storage_key")
