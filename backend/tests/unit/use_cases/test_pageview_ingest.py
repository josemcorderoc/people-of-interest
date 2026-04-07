"""Unit tests for pageview ingest use case."""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, patch

import pytest

from poi_people.application.use_cases.pageview_ingest import _s3_key_for_date, run_pageview_ingest
from poi_people.domain.entities.pageview_record import PageviewRecord
from poi_people.infrastructure.config.models import (
    AppConfig,
    PersonCategoryMapping,
    PipelineSettings,
)


@pytest.fixture
def mock_config() -> AppConfig:
    return AppConfig(
        language_editions=["en", "de"],
        person_categories=PersonCategoryMapping(p106_mapping={"Q82955": "politician"}),
        pipeline=PipelineSettings(
            retry_max_attempts=0,
            retry_backoff_minutes=[1],
            wikimedia_user_agent="Test/0.1",
            wikimedia_rate_limit_rps=1,
        ),
        s3_bucket="poi-pageview-dumps",
    )


@pytest.fixture
def mock_repos():
    person_repo = AsyncMock()
    person_repo.get_article_title_mapping.return_value = {"Barack Obama": "Q76"}
    pageview_repo = AsyncMock()
    pageview_repo.insert_batch.return_value = 1
    pipeline_repo = AsyncMock()
    pipeline_repo.insert.return_value = 1
    return person_repo, pageview_repo, pipeline_repo


class TestS3KeyForDate:
    def test_formats_date_correctly(self):
        d = datetime.date(2026, 4, 5)
        assert _s3_key_for_date(d) == "pageviews/pageviews-20260405-user.bz2"


class TestPageviewIngest:
    @pytest.mark.asyncio
    async def test_ingest_reads_and_inserts(self, mock_config, mock_repos):
        person_repo, pageview_repo, pipeline_repo = mock_repos
        date = datetime.date(2026, 4, 5)

        record = PageviewRecord(person_id="Q76", lang="en", date=date, views=5000)

        with patch(
            "poi_people.application.use_cases.pageview_ingest.read_pageviews_from_s3"
        ) as mock_read:
            mock_read.return_value = iter([record])

            total = await run_pageview_ingest(
                date=date,
                config=mock_config,
                s3_client=None,
                person_repo=person_repo,
                pageview_repo=pageview_repo,
                pipeline_repo=pipeline_repo,
            )

            assert total == 1
            pageview_repo.insert_batch.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_builds_title_map_for_all_langs(self, mock_config, mock_repos):
        person_repo, pageview_repo, pipeline_repo = mock_repos
        date = datetime.date(2026, 4, 5)

        with patch(
            "poi_people.application.use_cases.pageview_ingest.read_pageviews_from_s3"
        ) as mock_read:
            mock_read.return_value = iter([])

            await run_pageview_ingest(
                date=date,
                config=mock_config,
                s3_client=None,
                person_repo=person_repo,
                pageview_repo=pageview_repo,
                pipeline_repo=pipeline_repo,
            )

            # Should call get_article_title_mapping for each language
            assert person_repo.get_article_title_mapping.call_count == 2

    @pytest.mark.asyncio
    async def test_ingest_logs_success(self, mock_config, mock_repos):
        person_repo, pageview_repo, pipeline_repo = mock_repos
        date = datetime.date(2026, 4, 5)

        with patch(
            "poi_people.application.use_cases.pageview_ingest.read_pageviews_from_s3"
        ) as mock_read:
            mock_read.return_value = iter([])

            await run_pageview_ingest(
                date=date,
                config=mock_config,
                s3_client=None,
                person_repo=person_repo,
                pageview_repo=pageview_repo,
                pipeline_repo=pipeline_repo,
            )

            pipeline_repo.insert.assert_called_once()
            call_kwargs = pipeline_repo.update_status.call_args[1]
            assert call_kwargs["status"] == "success"
