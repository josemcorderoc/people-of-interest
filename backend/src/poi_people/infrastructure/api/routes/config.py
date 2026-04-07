"""Config endpoint — exposes public app configuration to the frontend."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["config"])


class ConfigResponse(BaseModel):
    """Public configuration returned to the frontend."""

    categories: list[str]
    languages: list[str]


@router.get("/config", response_model=ConfigResponse)
async def get_config(request: Request) -> ConfigResponse:
    """Return public application configuration.

    Includes available person categories and language editions.
    """
    app_config = request.app.state.config

    # Extract unique categories from the P106 mapping
    categories = sorted(set(app_config.person_categories.p106_mapping.values()))

    return ConfigResponse(
        categories=categories,
        languages=app_config.language_editions,
    )
