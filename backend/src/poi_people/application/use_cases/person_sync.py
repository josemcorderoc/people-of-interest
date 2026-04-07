"""Person sync use case — orchestrate Wikidata dump parsing + person persistence."""

from __future__ import annotations

import datetime
import logging
import time
from pathlib import Path

from poi_people.domain.entities.pipeline_run import PipelineRun
from poi_people.domain.repositories.person_repository import PersonRepository
from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository
from poi_people.infrastructure.adapters.wikidata_person_adapter import stream_persons_from_dump
from poi_people.infrastructure.config.models import AppConfig

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


async def run_person_sync(
    dump_path: Path,
    config: AppConfig,
    person_repo: PersonRepository,
    pipeline_repo: PipelineLogRepository,
    run_date: datetime.date | None = None,
) -> int:
    """Sync persons from a Wikidata dump into the database.

    Streams through the dump, batches Person entities, and upserts them.
    Logs pipeline run status and supports retry with backoff.

    Args:
        dump_path: Path to the gzipped Wikidata JSON dump.
        config: Application configuration.
        person_repo: Repository for persisting persons.
        pipeline_repo: Repository for logging pipeline runs.
        run_date: Date to record for this run (defaults to today).

    Returns:
        Total number of persons upserted.
    """
    if run_date is None:
        run_date = datetime.date.today()

    max_attempts = config.pipeline.retry_max_attempts + 1
    backoff_minutes = config.pipeline.retry_backoff_minutes

    for attempt in range(max_attempts):
        run = PipelineRun(
            stage="person_sync",
            run_date=run_date,
            status="running",
            started_at=datetime.datetime.now(datetime.UTC),
        )
        run_id = await pipeline_repo.insert(run)

        try:
            total = await _sync_persons(dump_path, config, person_repo)
            await pipeline_repo.update_status(
                run_id=run_id,
                status="success",
                finished_at=datetime.datetime.now(datetime.UTC),
                record_count=total,
            )
            logger.info("Person sync completed: %d persons upserted", total)
            return total

        except Exception as exc:
            await pipeline_repo.update_status(
                run_id=run_id,
                status="failed",
                finished_at=datetime.datetime.now(datetime.UTC),
                error_detail=str(exc),
            )
            if attempt < max_attempts - 1:
                wait = backoff_minutes[min(attempt, len(backoff_minutes) - 1)] * 60
                logger.warning(
                    "Person sync attempt %d failed: %s. Retrying in %ds...",
                    attempt + 1, exc, wait,
                )
                time.sleep(wait)
            else:
                logger.error("Person sync failed after %d attempts: %s", max_attempts, exc)
                raise

    return 0  # unreachable, but makes type-checker happy


async def _sync_persons(
    dump_path: Path,
    config: AppConfig,
    person_repo: PersonRepository,
) -> int:
    """Stream and batch-upsert persons from the dump."""
    total = 0
    batch = []

    for person in stream_persons_from_dump(
        dump_path=dump_path,
        languages=config.language_editions,
        category_mapping=config.person_categories,
    ):
        batch.append(person)
        if len(batch) >= BATCH_SIZE:
            count = await person_repo.upsert_batch(batch)
            total += count
            batch = []

    if batch:
        count = await person_repo.upsert_batch(batch)
        total += count

    return total
