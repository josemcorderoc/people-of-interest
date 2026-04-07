"""FastAPI application factory with lifespan, CORS, and structured logging."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from poi_people.infrastructure.api.routes import config as config_routes
from poi_people.infrastructure.api.routes import health as health_routes
from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.database.engine import create_engine, create_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize and tear down shared resources."""
    # Load config
    config_path = Path(os.environ.get("CONFIG_PATH", "config/settings.yaml"))
    app_config = load_config(config_path)
    app.state.config = app_config

    # Create database engine and session factory
    engine = create_engine()
    session_factory = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    logger.info("Application started with %d language editions", len(app_config.language_editions))

    yield

    # Shutdown
    await engine.dispose()
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A configured FastAPI instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    app = FastAPI(
        title="People of Interest API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Structured logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # Routes
    app.include_router(health_routes.router)
    app.include_router(config_routes.router)

    return app
