"""Atomic organization-level RAG quota reservations."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import settings
from app.core.database import SessionLocal
from app.models import RagUsagePeriod


class RagQuotaExceeded(RuntimeError):
    """The organization has exhausted a configured RAG operation quota."""


class RagQuotaUnavailable(RuntimeError):
    """The quota store could not safely authorize an RAG operation."""


def _reserve_period(
    db: Session,
    organization_id: UUID,
    period_type: str,
    period_start: date,
    limit: int,
) -> None:
    table = RagUsagePeriod.__table__
    statement = (
        insert(table)
        .values(
            id=uuid4(),
            organization_id=organization_id,
            period_type=period_type,
            period_start=period_start,
            operation_count=1,
        )
        .on_conflict_do_update(
            constraint="uq_rag_usage_period_organization_type_start",
            set_={"operation_count": table.c.operation_count + 1},
            where=table.c.operation_count < limit,
        )
        .returning(table.c.operation_count)
    )
    if db.execute(statement).scalar_one_or_none() is None:
        raise RagQuotaExceeded


def reserve_rag_operation(organization_id: UUID, now: datetime | None = None) -> None:
    """Commit one attempt before external work so failures still consume quota."""
    instant = now or datetime.now(UTC)
    if instant.tzinfo is None:
        raise ValueError("now debe incluir zona horaria")
    utc_day = instant.astimezone(UTC).date()
    utc_month = utc_day.replace(day=1)

    try:
        with SessionLocal.begin() as db:
            db.execute(
                delete(RagUsagePeriod).where(
                    RagUsagePeriod.organization_id == organization_id,
                    RagUsagePeriod.period_start < utc_day - timedelta(days=62),
                )
            )
            _reserve_period(
                db,
                organization_id,
                "day",
                utc_day,
                settings.RAG_DAILY_OPERATION_LIMIT,
            )
            _reserve_period(
                db,
                organization_id,
                "month",
                utc_month,
                settings.RAG_MONTHLY_OPERATION_LIMIT,
            )
    except SQLAlchemyError:
        raise RagQuotaUnavailable from None
