"""Unit tests for persons, person detail, and search API endpoints."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from poi_people.infrastructure.api.routes import person_detail as person_detail_routes
from poi_people.infrastructure.api.routes import persons as persons_routes
from poi_people.infrastructure.api.routes import search as search_routes
from poi_people.infrastructure.config.models import (
    AppConfig,
    PersonCategoryMapping,
    PipelineSettings,
)


@pytest.fixture
def mock_config() -> AppConfig:
    return AppConfig(
        language_editions=["en", "de"],
        person_categories=PersonCategoryMapping(
            p106_mapping={"Q82955": "politician", "Q937857": "athlete"}
        ),
        pipeline=PipelineSettings(
            retry_max_attempts=3,
            retry_backoff_minutes=[1, 5, 15],
            wikimedia_user_agent="Test/0.1",
            wikimedia_rate_limit_rps=1,
        ),
        s3_bucket="test",
    )


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory that returns an async context manager."""
    session = AsyncMock()

    factory = MagicMock()
    factory.return_value.__aenter__ = AsyncMock(return_value=session)
    factory.return_value.__aexit__ = AsyncMock(return_value=None)

    return factory, session


@pytest.fixture
def test_client(mock_config, mock_session_factory):
    factory, session = mock_session_factory
    app = FastAPI()
    app.state.config = mock_config
    app.state.session_factory = factory

    app.include_router(persons_routes.router)
    app.include_router(person_detail_routes.router)
    app.include_router(search_routes.router)

    return TestClient(app), session


class TestGetPersons:
    def test_returns_200(self, test_client):
        client, session = test_client

        # The endpoint makes multiple execute calls in sequence:
        # 1. max(date) -> returns a date
        # 2. count(*) -> returns int
        # 3. select rows -> returns list
        # 4. sparkline query -> returns list
        date_result = MagicMock()
        date_result.scalar.return_value = datetime.date(2026, 4, 5)

        count_result = MagicMock()
        count_result.scalar.return_value = 0

        rows_result = MagicMock()
        rows_result.all.return_value = []

        session.execute.side_effect = [date_result, count_result, rows_result]

        response = client.get("/api/persons")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["results"] == []

    def test_validates_view_param(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons?view=invalid")
        assert response.status_code == 422

    def test_validates_window_param(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons?window=invalid")
        assert response.status_code == 422

    def test_validates_page_min(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons?page=0")
        assert response.status_code == 422

    def test_validates_per_page_max(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons?per_page=500")
        assert response.status_code == 422


class TestGetPersonDetail:
    def test_returns_404_when_not_found(self, test_client):
        client, session = test_client
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        response = client.get("/api/persons/Q999/detail")
        assert response.status_code == 404

    def test_validates_window_param(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons/Q76/detail?window=invalid")
        assert response.status_code == 422


class TestSearchPersons:
    def test_requires_query_param(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons/search")
        assert response.status_code == 422

    def test_returns_200_with_query(self, test_client):
        client, session = test_client
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        response = client.get("/api/persons/search?q=obama")
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_validates_min_length(self, test_client):
        client, _ = test_client
        response = client.get("/api/persons/search?q=")
        assert response.status_code == 422
