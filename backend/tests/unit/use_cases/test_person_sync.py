"""Unit tests for person sync use case."""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from poi_people.application.use_cases.person_sync import run_person_sync
from poi_people.domain.entities.person import Person
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
def sample_person() -> Person:
    return Person(
        wikidata_id="Q76",
        name="Barack Obama",
        names_by_lang={"en": "Barack Obama"},
        article_titles={"en": "Barack Obama"},
        category="politician",
        birth_date=datetime.date(1961, 8, 4),
    )


@pytest.fixture
def mock_person_repo():
    repo = AsyncMock()
    repo.upsert_batch.return_value = 1
    return repo


@pytest.fixture
def mock_pipeline_repo():
    repo = AsyncMock()
    repo.insert.return_value = 1
    return repo


class TestPersonSync:
    @pytest.mark.asyncio
    async def test_sync_upserts_persons(
        self, mock_config, sample_person, mock_person_repo, mock_pipeline_repo
    ):
        with patch(
            "poi_people.application.use_cases.person_sync.stream_persons_from_dump"
        ) as mock_stream:
            mock_stream.return_value = iter([sample_person])

            total = await run_person_sync(
                dump_path=Path("/tmp/test.json.gz"),
                config=mock_config,
                person_repo=mock_person_repo,
                pipeline_repo=mock_pipeline_repo,
                run_date=datetime.date(2026, 4, 5),
            )

            assert total == 1
            mock_person_repo.upsert_batch.assert_called_once()
            batch = mock_person_repo.upsert_batch.call_args[0][0]
            assert len(batch) == 1
            assert batch[0].wikidata_id == "Q76"

    @pytest.mark.asyncio
    async def test_sync_logs_pipeline_run(
        self, mock_config, mock_person_repo, mock_pipeline_repo
    ):
        with patch(
            "poi_people.application.use_cases.person_sync.stream_persons_from_dump"
        ) as mock_stream:
            mock_stream.return_value = iter([])

            await run_person_sync(
                dump_path=Path("/tmp/test.json.gz"),
                config=mock_config,
                person_repo=mock_person_repo,
                pipeline_repo=mock_pipeline_repo,
            )

            mock_pipeline_repo.insert.assert_called_once()
            mock_pipeline_repo.update_status.assert_called_once()
            call_kwargs = mock_pipeline_repo.update_status.call_args[1]
            assert call_kwargs["status"] == "success"

    @pytest.mark.asyncio
    async def test_sync_logs_failure(
        self, mock_config, mock_person_repo, mock_pipeline_repo
    ):
        with patch(
            "poi_people.application.use_cases.person_sync.stream_persons_from_dump"
        ) as mock_stream:
            mock_stream.side_effect = RuntimeError("dump not found")

            with pytest.raises(RuntimeError, match="dump not found"):
                await run_person_sync(
                    dump_path=Path("/tmp/test.json.gz"),
                    config=mock_config,
                    person_repo=mock_person_repo,
                    pipeline_repo=mock_pipeline_repo,
                )

            call_kwargs = mock_pipeline_repo.update_status.call_args[1]
            assert call_kwargs["status"] == "failed"
            assert "dump not found" in call_kwargs["error_detail"]

    @pytest.mark.asyncio
    async def test_sync_batches_persons(
        self, mock_config, sample_person, mock_person_repo, mock_pipeline_repo
    ):
        """Test that large numbers of persons are batched."""
        persons = [
            Person(
                wikidata_id=f"Q{i}",
                name=f"Person {i}",
                names_by_lang={"en": f"Person {i}"},
                article_titles={"en": f"Person {i}"},
                category="politician",
            )
            for i in range(1200)
        ]

        with patch(
            "poi_people.application.use_cases.person_sync.stream_persons_from_dump"
        ) as mock_stream:
            mock_stream.return_value = iter(persons)
            mock_person_repo.upsert_batch.return_value = 500

            total = await run_person_sync(
                dump_path=Path("/tmp/test.json.gz"),
                config=mock_config,
                person_repo=mock_person_repo,
                pipeline_repo=mock_pipeline_repo,
            )

            # 1200 persons / 500 batch = 3 batches (500+500+200)
            assert mock_person_repo.upsert_batch.call_count == 3
            assert total == 1500  # 500 returned each of 3 calls
