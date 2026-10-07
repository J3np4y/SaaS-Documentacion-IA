"""User identity and password hash."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class User(Base):
    """A login identity; organization access is assigned through Membership."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),)

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    membership: Mapped["Membership"] = relationship(back_populates="user", uselist=False)


from app.models.membership import Membership
