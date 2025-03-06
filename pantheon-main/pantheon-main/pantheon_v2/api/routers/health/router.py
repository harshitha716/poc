from fastapi import APIRouter
from pantheon_v2.api.routers.health.schemas.health import HealthResponse

router = APIRouter(prefix="/health")


@router.get("/")
async def health() -> HealthResponse:
    return HealthResponse(status="pantheon_v2 is ok")
