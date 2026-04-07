"""Score computation use case — batch SQL popularity + z-score calculation."""

from __future__ import annotations

import datetime
import logging
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poi_people.domain.entities.pipeline_run import PipelineRun
from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository
from poi_people.infrastructure.config.models import AppConfig

logger = logging.getLogger(__name__)

# Window definitions: name -> number of days to look back for SUM(views)
WINDOW_DAYS = {
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
}

# Z-score lookback: 30 days of historical daily popularity for mean/stddev
ZSCORE_LOOKBACK_DAYS = 30


async def run_score_compute(
    date: datetime.date,
    config: AppConfig,
    session_factory: async_sessionmaker[AsyncSession],
    pipeline_repo: PipelineLogRepository,
) -> int:
    """Compute popularity and trending z-scores for all persons on a date.

    Uses batch SQL (INSERT INTO scores_daily SELECT...) for efficiency.

    Args:
        date: The date to compute scores for.
        config: Application configuration.
        session_factory: Async session factory.
        pipeline_repo: Repository for logging pipeline runs.

    Returns:
        Total number of score records inserted/updated.
    """
    max_attempts = config.pipeline.retry_max_attempts + 1
    backoff_minutes = config.pipeline.retry_backoff_minutes

    for attempt in range(max_attempts):
        run = PipelineRun(
            stage="score_compute",
            run_date=date,
            status="running",
            started_at=datetime.datetime.now(datetime.UTC),
        )
        run_id = await pipeline_repo.insert(run)

        try:
            total = await _compute_scores(date, session_factory)
            await pipeline_repo.update_status(
                run_id=run_id,
                status="success",
                finished_at=datetime.datetime.now(datetime.UTC),
                record_count=total,
            )
            logger.info("Score compute for %s completed: %d records", date, total)
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
                    "Score compute attempt %d failed: %s. Retrying in %ds...",
                    attempt + 1, exc, wait,
                )
                time.sleep(wait)
            else:
                logger.error("Score compute failed after %d attempts: %s", max_attempts, exc)
                raise

    return 0


async def _compute_scores(
    date: datetime.date,
    session_factory: async_sessionmaker[AsyncSession],
) -> int:
    """Execute batch SQL to compute popularity and z-scores for each window."""
    total = 0

    async with session_factory() as session:
        for window_name, window_days in WINDOW_DAYS.items():
            start_date = date - datetime.timedelta(days=window_days - 1)

            # Step 1: Compute popularity = SUM(views) per person for the window
            # Step 2: Compute z-score = (today_popularity - mean_30d) / stddev_30d
            # Using a single INSERT ... ON CONFLICT query
            sql = text("""
                INSERT INTO scores_daily (person_id, date, window, popularity, trending_zscore)
                SELECT
                    pop.person_id,
                    :score_date AS date,
                    :window AS window,
                    pop.popularity,
                    CASE
                        WHEN hist.stddev_pop IS NULL OR hist.stddev_pop = 0 THEN NULL
                        ELSE (pop.popularity - hist.mean_pop) / hist.stddev_pop
                    END AS trending_zscore
                FROM (
                    -- Current window popularity
                    SELECT person_id, COALESCE(SUM(views), 0)::bigint AS popularity
                    FROM pageviews_daily
                    WHERE date >= :window_start AND date <= :score_date
                    GROUP BY person_id
                ) pop
                LEFT JOIN (
                    -- 30-day historical stats for z-score
                    SELECT
                        person_id,
                        AVG(daily_total)::float AS mean_pop,
                        STDDEV_POP(daily_total)::float AS stddev_pop
                    FROM (
                        SELECT person_id, date, SUM(views) AS daily_total
                        FROM pageviews_daily
                        WHERE date >= :zscore_start AND date < :score_date
                        GROUP BY person_id, date
                    ) daily_sums
                    GROUP BY person_id
                ) hist ON pop.person_id = hist.person_id
                ON CONFLICT (person_id, date, window)
                DO UPDATE SET
                    popularity = EXCLUDED.popularity,
                    trending_zscore = EXCLUDED.trending_zscore
            """)

            zscore_start = date - datetime.timedelta(days=ZSCORE_LOOKBACK_DAYS)

            result = await session.execute(sql, {
                "score_date": date,
                "window": window_name,
                "window_start": start_date,
                "zscore_start": zscore_start,
            })
            total += result.rowcount

        await session.commit()

    return total
