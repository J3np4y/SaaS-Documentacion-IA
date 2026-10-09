"""Organization-scoped UTC usage counters for RAG operations."""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class RagUsagePeriod(Base):
    """An atomic operation counter for one organization and UTC period."""

    __tablename__ = "rag_usage_periods"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "period_type",
            "period_start",
            name="uq_rag_usage_period_organization_type_start",
        ),
        CheckConstraint("period_type IN ('day', 'month')", name="ck_rag_usage_period_type"),
        CheckConstraint("operation_count > 0", name="ck_rag_usage_operation_count_positive"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_type: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    operation_count: Mapped[int] = mapped_column(Integer, nullable=False)
