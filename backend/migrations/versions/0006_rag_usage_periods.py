"""Add atomic daily and monthly RAG operation counters."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_rag_usage_periods"
down_revision: str | None = "0005_rag_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rag_usage_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_type", sa.String(length=8), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("operation_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "period_type IN ('day', 'month')",
            name="ck_rag_usage_period_type",
        ),
        sa.CheckConstraint(
            "operation_count > 0",
            name="ck_rag_usage_operation_count_positive",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "period_type",
            "period_start",
            name="uq_rag_usage_period_organization_type_start",
        ),
    )
    op.create_index(
        "ix_rag_usage_periods_organization_id",
        "rag_usage_periods",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_rag_usage_periods_organization_id", table_name="rag_usage_periods")
    op.drop_table("rag_usage_periods")
