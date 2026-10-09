from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.organizations import router as organizations_router
from app.core.database import dispose_engine
from app.services.document_storage import MAX_UPLOAD_REQUEST_BYTES


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
app.include_router(documents_router)


@app.middleware("http")
async def limit_document_upload_request(
    request: Request, call_next: RequestResponseEndpoint
) -> Response:
    if request.method == "POST" and request.url.path == "/organizations/me/documents":
        content_length = request.headers.get("content-length")
        if content_length is None:
            return JSONResponse(
                status_code=411,
                content={"detail": "La solicitud debe indicar su tamaño"},
            )
        try:
            request_size = int(content_length)
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Tamaño de solicitud no válido"})
        if request_size > MAX_UPLOAD_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={"detail": "La solicitud de carga supera el límite permitido"},
            )
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, __: RequestValidationError) -> JSONResponse:
    """Avoid echoing submitted secrets in FastAPI's default validation details."""
    return JSONResponse(
        status_code=422,
        content={"detail": "Solicitud no válida"},
    )
