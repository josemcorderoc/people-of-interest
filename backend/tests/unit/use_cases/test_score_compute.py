"""Unit tests for score compute use case."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from poi_people.application.use_cases.score_compute import WINDOW_DAYS, run_score_compute
from poi_people.infrastructure.config.models import (
    AppConfig,
    PersonCategoryMapping,
    PipelineSettings,
)


@pytest.fixture
def mock_config() -> AppConfig:
    return AppConfig(
        language_editions=["en"],
        person_categories=PersonCategoryMapping(p106_mapping={"Q82955": "politician"}),
        pipeline=PipelineSettings(
            retry_max_attempts=0,
            retry_backoff_minutes=[1],
            wikimedia_user_agent="Test/0.1",
            wikimedia_rate_limit_rps=1,
        ),
        s3_bucket="test",
    )


@pytest.fixture
def mock_pipeline_repo():
    repo = AsyncMock()
    repo.insert.return_value = 1
    return repo


class TestWindowDays:
    def test_daily_is_1(self):
        assert WINDOW_DAYS["daily"] == 1

    def test_weekly_is_7(self):
        assert WINDOW_DAYS["weekly"] == 7

    def test_monthly_is_30(self):
        assert WINDOW_DAYS["monthly"] == 30


class TestScoreCompute:
    @pytest.mark.asyncio
    async def test_compute_logs_pipeline_run(self, mock_config, mock_pipeline_repo):
        # Mock session factory
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 10
        mock_session.execute.return_value = mock_result

        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        total = await run_score_compute(
            date=datetime.date(2026, 4, 5),
            config=mock_config,
            session_factory=mock_session_factory,
            pipeline_repo=mock_pipeline_repo,
        )

        mock_pipeline_repo.insert.assert_called_once()
        call_kwargs = mock_pipeline_repo.update_status.call_args[1]
        assert call_kwargs["status"] == "success"
        # 3 windows * 10 rowcount each = 30
        assert total == 30

    @pytest.mark.asyncio
    async def test_compute_executes_sql_for_each_window(self, mock_config, mock_pipeline_repo):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        mock_session_factory = MagicMock()
        mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

        await run_score_compute(
            date=datetime.date(2026, 4, 5),
            config=mock_config,
            session_factory=mock_session_factory,
            pipeline_repo=mock_pipeline_repo,
        )

        # 3 windows + 1 commit
        assert mock_session.execute.call_count == 3
        mock_session.commit.assert_called_once()
