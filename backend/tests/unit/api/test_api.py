"""Unit tests for FastAPI application and routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from poi_people.infrastructure.config.models import (
    AppConfig,
    PersonCategoryMapping,
    PipelineSettings,
)


@pytest.fixture
def mock_config() -> AppConfig:
    """Create a mock AppConfig for testing."""
    return AppConfig(
        language_editions=["en", "ja", "de", "es", "fr"],
        person_categories=PersonCategoryMapping(
            p106_mapping={
                "Q82955": "politician",
                "Q937857": "athlete",
                "Q177220": "artist",
                "Q169470": "scientist",
                "Q43845": "business",
                "Q36180": "writer",
            }
        ),
        pipeline=PipelineSettings(
            retry_max_attempts=3,
            retry_backoff_minutes=[1, 5, 15],
            wikimedia_user_agent="Test/0.1",
            wikimedia_rate_limit_rps=1,
        ),
        s3_bucket="test-bucket",
    )


@pytest.fixture
def test_client(mock_config: AppConfig) -> TestClient:
    """Create a TestClient that skips the lifespan (no DB needed)."""
    from fastapi import FastAPI

    from poi_people.infrastructure.api.routes import config as config_routes
    from poi_people.infrastructure.api.routes import health as health_routes

    app = FastAPI()
    app.state.config = mock_config
    app.include_router(health_routes.router)
    app.include_router(config_routes.router)

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_200(self, test_client: TestClient) -> None:
        response = test_client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, test_client: TestClient) -> None:
        response = test_client.get("/api/health")
        assert response.json() == {"status": "ok"}


class TestConfigEndpoint:
    """Tests for GET /api/config."""

    def test_config_returns_200(self, test_client: TestClient) -> None:
        response = test_client.get("/api/config")
        assert response.status_code == 200

    def test_config_contains_languages(self, test_client: TestClient) -> None:
        data = test_client.get("/api/config").json()
        assert data["languages"] == ["en", "ja", "de", "es", "fr"]

    def test_config_contains_categories(self, test_client: TestClient) -> None:
        data = test_client.get("/api/config").json()
        cats = data["categories"]
        assert "politician" in cats
        assert "athlete" in cats
        assert "artist" in cats
        assert "scientist" in cats
        assert "business" in cats
        assert "writer" in cats

    def test_categories_are_sorted(self, test_client: TestClient) -> None:
        data = test_client.get("/api/config").json()
        cats = data["categories"]
        assert cats == sorted(cats)

    def test_categories_are_deduplicated(self, test_client: TestClient) -> None:
        data = test_client.get("/api/config").json()
        cats = data["categories"]
        assert len(cats) == len(set(cats))


class TestAppFactory:
    """Tests for the create_app factory."""

    def test_create_app_returns_fastapi(self) -> None:
        """Test that create_app produces a FastAPI instance (without starting lifespan)."""
        from fastapi import FastAPI

        from poi_people.infrastructure.api.app import create_app

        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "People of Interest API"

    def test_app_has_health_route(self) -> None:
        from poi_people.infrastructure.api.app import create_app

        app = create_app()
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/health" in routes

    def test_app_has_config_route(self) -> None:
        from poi_people.infrastructure.api.app import create_app

        app = create_app()
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/config" in routes
