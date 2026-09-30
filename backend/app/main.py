from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
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
