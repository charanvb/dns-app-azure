"""Health-check router used as liveness and readiness probe by Container Apps."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Schema returned by the health probe."""

    status: str
    version: str
    environment: str


@router.get("", response_model=HealthResponse, summary="Liveness probe")
async def health_check() -> HealthResponse:
    """Return HTTP 200 while the process is alive."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )
