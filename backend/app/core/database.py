"""SQLAlchemy engine and request-scoped session lifecycle."""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core import settings  # noqa: F401  (loads local .env for development)
from app.models import Base


def _database_url() -> str:
    """Read the database URL from the process environment, never log it."""
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL no está configurada")
    return value


def _create_engine() -> Engine:
    return create_engine(_database_url(), pool_pre_ping=True)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and always close it afterward."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def dispose_engine() -> None:
    """Close idle pooled connections during application shutdown."""
    engine.dispose()


__all__ = ["Base", "Session", "engine", "get_db"]
