"""CLI entrypoint for person sync pipeline stage."""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
from pathlib import Path

from poi_people.application.use_cases.person_sync import run_person_sync
from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.database.engine import create_engine, create_session_factory
from poi_people.infrastructure.database.person_repository import SqlPersonRepository
from poi_people.infrastructure.database.pipeline_log_repository import SqlPipelineLogRepository


def main() -> None:
    """Run person sync from a Wikidata dump."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Sync persons from Wikidata dump")
    parser.add_argument("dump_path", type=Path, help="Path to gzipped Wikidata JSON dump")
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"), help="Config file path")
    parser.add_argument("--date", type=str, default=None, help="Run date (YYYY-MM-DD), defaults to today")
    args = parser.parse_args()

    config = load_config(args.config)
    run_date = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()

    asyncio.run(_run(args.dump_path, config, run_date))


async def _run(dump_path: Path, config, run_date: datetime.date) -> None:
    engine = create_engine()
    session_factory = create_session_factory(engine)

    person_repo = SqlPersonRepository(session_factory)
    pipeline_repo = SqlPipelineLogRepository(session_factory)

    try:
        total = await run_person_sync(
            dump_path=dump_path,
            config=config,
            person_repo=person_repo,
            pipeline_repo=pipeline_repo,
            run_date=run_date,
        )
        print(f"Person sync complete: {total} persons upserted")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    main()
