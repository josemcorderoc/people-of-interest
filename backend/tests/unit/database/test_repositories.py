"""Unit tests for database repository implementations using mocks."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestSqlPersonRepository:
    """Tests for SqlPersonRepository."""

    def test_satisfies_protocol(self) -> None:
        """SqlPersonRepository should satisfy the PersonRepository protocol."""
        from poi_people.domain.repositories.person_repository import PersonRepository
        from poi_people.infrastructure.database.person_repository import SqlPersonRepository

        repo = SqlPersonRepository(session_factory=MagicMock())
        assert isinstance(repo, PersonRepository)

    @pytest.mark.asyncio
    async def test_upsert_batch_empty_returns_zero(self) -> None:
        from poi_people.infrastructure.database.person_repository import SqlPersonRepository

        repo = SqlPersonRepository(session_factory=MagicMock())
        result = await repo.upsert_batch([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        from poi_people.infrastructure.database.person_repository import SqlPersonRepository

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Build an async context manager that yields mock_session
        ctx = AsyncMock()
        ctx.__aenter__.return_value = mock_session
        ctx.__aexit__.return_value = False

        mock_factory = MagicMock()
        mock_factory.return_value = ctx

        repo = SqlPersonRepository(session_factory=mock_factory)
        result = await repo.get_by_id("Q99999")
        assert result is None


class TestSqlPageviewRepository:
    """Tests for SqlPageviewRepository."""

    def test_satisfies_protocol(self) -> None:
        from poi_people.domain.repositories.pageview_repository import PageviewRepository
        from poi_people.infrastructure.database.pageview_repository import SqlPageviewRepository

        repo = SqlPageviewRepository(session_factory=MagicMock())
        assert isinstance(repo, PageviewRepository)

    @pytest.mark.asyncio
    async def test_insert_batch_empty_returns_zero(self) -> None:
        from poi_people.infrastructure.database.pageview_repository import SqlPageviewRepository

        repo = SqlPageviewRepository(session_factory=MagicMock())
        result = await repo.insert_batch([])
        assert result == 0


class TestSqlScoreRepository:
    """Tests for SqlScoreRepository."""

    def test_satisfies_protocol(self) -> None:
        from poi_people.domain.repositories.score_repository import ScoreRepository
        from poi_people.infrastructure.database.score_repository import SqlScoreRepository

        repo = SqlScoreRepository(session_factory=MagicMock())
        assert isinstance(repo, ScoreRepository)

    @pytest.mark.asyncio
    async def test_insert_batch_empty_returns_zero(self) -> None:
        from poi_people.infrastructure.database.score_repository import SqlScoreRepository

        repo = SqlScoreRepository(session_factory=MagicMock())
        result = await repo.insert_batch([])
        assert result == 0

    @pytest.mark.asyncio
    async def test_get_ranked_rejects_invalid_column(self) -> None:
        from poi_people.infrastructure.database.score_repository import SqlScoreRepository

        repo = SqlScoreRepository(session_factory=MagicMock())
        with pytest.raises(ValueError, match="Invalid score_column"):
            await repo.get_ranked(
                window="daily",
                score_date=datetime.date(2026, 4, 1),
                score_column="sql_injection; DROP TABLE",
            )


class TestSqlPipelineLogRepository:
    """Tests for SqlPipelineLogRepository."""

    def test_satisfies_protocol(self) -> None:
        from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository
        from poi_people.infrastructure.database.pipeline_log_repository import SqlPipelineLogRepository

        repo = SqlPipelineLogRepository(session_factory=MagicMock())
        assert isinstance(repo, PipelineLogRepository)


class TestDatabaseEngine:
    """Tests for the engine module."""

    def test_get_database_url_raises_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from poi_people.infrastructure.database.engine import get_database_url

        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            get_database_url()

    def test_get_database_url_reads_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from poi_people.infrastructure.database.engine import get_database_url

        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
        assert get_database_url() == "postgresql+asyncpg://test:test@localhost/test"

    def test_create_engine_with_explicit_url(self) -> None:
        from poi_people.infrastructure.database.engine import create_engine

        engine = create_engine("postgresql+asyncpg://test:test@localhost/testdb")
        assert engine is not None
        assert engine.url.database == "testdb"
        assert engine.url.drivername == "postgresql+asyncpg"

    def test_create_session_factory(self) -> None:
        from poi_people.infrastructure.database.engine import create_engine, create_session_factory

        engine = create_engine("postgresql+asyncpg://test:test@localhost/testdb")
        factory = create_session_factory(engine)
        assert factory is not None
