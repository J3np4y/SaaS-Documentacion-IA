from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Estado de la API")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Disponibilidad de API y base de datos")
def readiness(db: Annotated[Session, Depends(get_db)]) -> dict[str, str]:
    """Report readiness only when PostgreSQL accepts a simple query."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # Keep driver details and connection information out of the response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio no disponible",
        ) from exc
    return {"status": "ready"}
