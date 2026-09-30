"""Persistence models and declarative SQLAlchemy metadata."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class used by ORM models and Alembic metadata discovery."""


from app.models.document import Document
from app.models.organization import Organization

__all__ = ["Base", "Document", "Organization"]
