"""Shared fixtures for tests that require the isolated PostgreSQL database."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core import settings  # noqa: F401  (loads .env and derives local URLs)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


@pytest.fixture()
def migrated_database():
    """Apply migrations to, and reset, only the dedicated disposable test database."""
    if not TEST_DATABASE_URL:
        pytest.skip("Define TEST_DATABASE_URL para las pruebas PostgreSQL")
    if make_url(TEST_DATABASE_URL).database != "docs_assistant_test":
        pytest.fail("TEST_DATABASE_URL debe apuntar a la base docs_assistant_test")

    environment = os.environ.copy()
    environment["DATABASE_URL"] = TEST_DATABASE_URL
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env=environment,
        capture_output=True,
        text=True,
    )
    engine = create_engine(TEST_DATABASE_URL)
    try:
        yield engine
    finally:
        with engine.begin() as connection:
            connection.execute(text("DROP SCHEMA public CASCADE"))
            connection.execute(text("CREATE SCHEMA public"))
        engine.dispose()
