from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.api.health import get_db
from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_returns_ready_when_database_answers() -> None:
    session = Mock()
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    session.execute.assert_called_once()


def test_readiness_hides_database_error_details() -> None:
    session = Mock()
    session.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("password=super-secret")
    )
    app.dependency_overrides[get_db] = lambda: session
    try:
        response = client.get("/ready")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Servicio no disponible"}
    assert "super-secret" not in response.text
