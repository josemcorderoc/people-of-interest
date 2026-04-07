"""CLI entrypoint for pageview ingest pipeline stage."""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
from pathlib import Path

import boto3

from poi_people.application.use_cases.pageview_ingest import run_pageview_ingest
from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.database.engine import create_engine, create_session_factory
from poi_people.infrastructure.database.pageview_repository import SqlPageviewRepository
from poi_people.infrastructure.database.person_repository import SqlPersonRepository
from poi_people.infrastructure.database.pipeline_log_repository import SqlPipelineLogRepository


def main() -> None:
    """Ingest pageviews for a given date from S3."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Ingest pageviews from S3")
    parser.add_argument("date", type=str, help="Date to ingest (YYYY-MM-DD)")
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"), help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    ingest_date = datetime.date.fromisoformat(args.date)

    asyncio.run(_run(ingest_date, config))


async def _run(ingest_date: datetime.date, config) -> None:
    engine = create_engine()
    session_factory = create_session_factory(engine)
    s3_client = boto3.client("s3")

    person_repo = SqlPersonRepository(session_factory)
    pageview_repo = SqlPageviewRepository(session_factory)
    pipeline_repo = SqlPipelineLogRepository(session_factory)

    try:
        total = await run_pageview_ingest(
            date=ingest_date,
            config=config,
            s3_client=s3_client,
            person_repo=person_repo,
            pageview_repo=pageview_repo,
            pipeline_repo=pipeline_repo,
        )
        print(f"Pageview ingest complete: {total} records inserted")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    main()
