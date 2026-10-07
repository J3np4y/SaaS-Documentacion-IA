"""Organization membership and role."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Membership(Base):
    """The user's role inside their single organization."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_memberships_user_id"),
        UniqueConstraint("organization_id", "user_id", name="uq_memberships_org_user"),
        CheckConstraint("role IN ('owner', 'member')", name="ck_memberships_role"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    user: Mapped["User"] = relationship(back_populates="membership")


from app.models.user import User
