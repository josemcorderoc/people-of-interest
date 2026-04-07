"""CLI entrypoint for score computation pipeline stage."""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
from pathlib import Path

from poi_people.application.use_cases.score_compute import run_score_compute
from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.database.engine import create_engine, create_session_factory
from poi_people.infrastructure.database.pipeline_log_repository import SqlPipelineLogRepository


def main() -> None:
    """Compute popularity and trending scores for a given date."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Compute scores")
    parser.add_argument("date", type=str, help="Date to compute scores for (YYYY-MM-DD)")
    parser.add_argument("--config", type=Path, default=Path("config/settings.yaml"), help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    score_date = datetime.date.fromisoformat(args.date)

    asyncio.run(_run(score_date, config))


async def _run(score_date: datetime.date, config) -> None:
    engine = create_engine()
    session_factory = create_session_factory(engine)

    pipeline_repo = SqlPipelineLogRepository(session_factory)

    try:
        total = await run_score_compute(
            date=score_date,
            config=config,
            session_factory=session_factory,
            pipeline_repo=pipeline_repo,
        )
        print(f"Score compute complete: {total} score records")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    main()
