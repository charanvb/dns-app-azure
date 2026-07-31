"""Health check and configuration API."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings

router = APIRouter(prefix="/api", tags=["api-health"])


@router.get("/health", summary="Health check endpoint")
async def health_check() -> JSONResponse:
    """Return API health status and configuration."""
    return JSONResponse({
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    })
