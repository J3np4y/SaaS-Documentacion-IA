from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.organizations import router as organizations_router
from app.core.database import dispose_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Release pooled database connections when the API shuts down."""
    yield
    dispose_engine()

app = FastAPI(
    title="Docs Assistant API",
    description="API de la plataforma de documentación empresarial con IA.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(organizations_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, __: RequestValidationError) -> JSONResponse:
    """Avoid echoing submitted secrets in FastAPI's default validation details."""
    return JSONResponse(
        status_code=422,
        content={"detail": "Solicitud no válida"},
    )
