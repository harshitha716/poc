from fastapi import APIRouter
from .schemas.health import HealthResponse

router = APIRouter(prefix="/health")


@router.get("/")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
