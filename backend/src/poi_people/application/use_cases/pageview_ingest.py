"""Pageview ingest use case — read S3 dumps, filter to known persons, bulk insert."""

from __future__ import annotations

import datetime
import logging
import time

from poi_people.domain.entities.pageview_record import PageviewRecord
from poi_people.domain.entities.pipeline_run import PipelineRun
from poi_people.domain.repositories.pageview_repository import PageviewRepository
from poi_people.domain.repositories.person_repository import PersonRepository
from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository
from poi_people.infrastructure.adapters.s3_pageview_reader import read_pageviews_from_s3
from poi_people.infrastructure.config.models import AppConfig

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def _s3_key_for_date(date: datetime.date) -> str:
    """Build the S3 object key for a given date's pageview dump.

    Wikimedia pageview_complete dumps follow:
    pageviews/pageviews-YYYYMMDD-user.bz2
    """
    return f"pageviews/pageviews-{date.strftime('%Y%m%d')}-user.bz2"


async def run_pageview_ingest(
    date: datetime.date,
    config: AppConfig,
    s3_client,
    person_repo: PersonRepository,
    pageview_repo: PageviewRepository,
    pipeline_repo: PipelineLogRepository,
) -> int:
    """Ingest pageviews for a single date from S3.

    Reads the bz2-compressed dump, filters to persons in the registry,
    and bulk-inserts matching records.

    Args:
        date: The date to ingest pageviews for.
        config: Application configuration.
        s3_client: A boto3 S3 client.
        person_repo: Repository for person lookups.
        pageview_repo: Repository for inserting pageview records.
        pipeline_repo: Repository for logging pipeline runs.

    Returns:
        Total number of pageview records inserted.
    """
    max_attempts = config.pipeline.retry_max_attempts + 1
    backoff_minutes = config.pipeline.retry_backoff_minutes

    for attempt in range(max_attempts):
        run = PipelineRun(
            stage="pageview_ingest",
            run_date=date,
            status="running",
            started_at=datetime.datetime.now(datetime.UTC),
        )
        run_id = await pipeline_repo.insert(run)

        try:
            total = await _ingest(date, config, s3_client, person_repo, pageview_repo)
            await pipeline_repo.update_status(
                run_id=run_id,
                status="success",
                finished_at=datetime.datetime.now(datetime.UTC),
                record_count=total,
            )
            logger.info("Pageview ingest for %s completed: %d records", date, total)
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
                    "Pageview ingest attempt %d failed: %s. Retrying in %ds...",
                    attempt + 1, exc, wait,
                )
                time.sleep(wait)
            else:
                logger.error("Pageview ingest failed after %d attempts: %s", max_attempts, exc)
                raise

    return 0


async def _ingest(
    date: datetime.date,
    config: AppConfig,
    s3_client,
    person_repo: PersonRepository,
    pageview_repo: PageviewRepository,
) -> int:
    """Core ingest logic: build title map, stream S3, batch insert."""
    # Build article_title -> wikidata_id mapping across all languages
    title_to_person: dict[str, str] = {}
    target_langs = set(config.language_editions)

    for lang in config.language_editions:
        mapping = await person_repo.get_article_title_mapping(lang)
        title_to_person.update(mapping)

    key = _s3_key_for_date(date)

    total = 0
    batch: list[PageviewRecord] = []

    for record in read_pageviews_from_s3(
        s3_client=s3_client,
        bucket=config.s3_bucket,
        key=key,
        date=date,
        title_to_person_id=title_to_person,
        target_langs=target_langs,
    ):
        batch.append(record)
        if len(batch) >= BATCH_SIZE:
            count = await pageview_repo.insert_batch(batch)
            total += count
            batch = []

    if batch:
        count = await pageview_repo.insert_batch(batch)
        total += count

    return total
