"""Persistence models and declarative SQLAlchemy metadata."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class used by ORM models and Alembic metadata discovery."""


from app.models.auth_session import AuthSession
from app.models.document import Document
from app.models.invitation import Invitation
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User

__all__ = ["AuthSession", "Base", "Document", "Invitation", "Membership", "Organization", "User"]
