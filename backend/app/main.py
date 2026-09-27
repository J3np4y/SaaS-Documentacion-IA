from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(
    title="Docs Assistant API",
    description="API de la plataforma de documentación empresarial con IA.",
    version="0.1.0",
)
app.include_router(health_router)
