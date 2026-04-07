"""CLI entrypoint for backfill — orchestrates person sync, pageview ingest, and score compute."""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
from pathlib import Path

import boto3

from poi_people.application.use_cases.pageview_ingest import run_pageview_ingest
from poi_people.application.use_cases.person_sync import run_person_sync
from poi_people.application.use_cases.score_compute import run_score_compute
from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.database.engine import create_engine, create_session_factory
from poi_people.infrastructure.database.pageview_repository import SqlPageviewRepository
from poi_people.infrastructure.database.person_repository import SqlPersonRepository
from poi_people.infrastructure.database.pipeline_log_repository import SqlPipelineLogRepository

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the full backfill pipeline: person sync -> pageview ingest (per day) -> score compute."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Backfill pipeline")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--dump-path", type=Path, default=None, help="Wikidata dump path (skip person sync if omitted)")
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"), help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    start = datetime.date.fromisoformat(args.start_date)
    end = datetime.date.fromisoformat(args.end_date)

    if start > end:
        parser.error("--start-date must be <= --end-date")

    asyncio.run(_run(start, end, args.dump_path, config))


async def _run(
    start: datetime.date,
    end: datetime.date,
    dump_path: Path | None,
    config,
) -> None:
    engine = create_engine()
    session_factory = create_session_factory(engine)
    s3_client = boto3.client("s3")

    person_repo = SqlPersonRepository(session_factory)
    pageview_repo = SqlPageviewRepository(session_factory)
    pipeline_repo = SqlPipelineLogRepository(session_factory)

    try:
        # Step 1: Person sync (if dump provided)
        if dump_path is not None:
            logger.info("Starting person sync from %s", dump_path)
            total = await run_person_sync(
                dump_path=dump_path,
                config=config,
                person_repo=person_repo,
                pipeline_repo=pipeline_repo,
                run_date=start,
            )
            logger.info("Person sync done: %d persons", total)

        # Step 2: Pageview ingest for each day
        current = start
        while current <= end:
            logger.info("Ingesting pageviews for %s", current)
            try:
                total = await run_pageview_ingest(
                    date=current,
                    config=config,
                    s3_client=s3_client,
                    person_repo=person_repo,
                    pageview_repo=pageview_repo,
                    pipeline_repo=pipeline_repo,
                )
                logger.info("Pageview ingest for %s: %d records", current, total)
            except Exception:
                logger.exception("Failed to ingest pageviews for %s, continuing...", current)
            current += datetime.timedelta(days=1)

        # Step 3: Score compute for each day
        current = start
        while current <= end:
            logger.info("Computing scores for %s", current)
            try:
                total = await run_score_compute(
                    date=current,
                    config=config,
                    session_factory=session_factory,
                    pipeline_repo=pipeline_repo,
                )
                logger.info("Score compute for %s: %d records", current, total)
            except Exception:
                logger.exception("Failed to compute scores for %s, continuing...", current)
            current += datetime.timedelta(days=1)

        logger.info("Backfill complete for %s to %s", start, end)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    main()
