"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check() -> dict:
    """Return a simple health check response.

    Returns:
        JSON with status "ok".
    """
    return {"status": "ok"}
