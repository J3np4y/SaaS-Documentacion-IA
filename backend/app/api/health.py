from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Estado de la API")
def health() -> dict[str, str]:
    return {"status": "ok"}
