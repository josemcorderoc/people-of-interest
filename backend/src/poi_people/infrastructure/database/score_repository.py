"""SQLAlchemy implementation of the ScoreRepository protocol."""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poi_people.domain.entities.score_record import ScoreRecord
from poi_people.infrastructure.database import models


class SqlScoreRepository:
    """SQLAlchemy-backed ScoreRepository implementation."""

    _SORTABLE_COLUMNS = {"popularity", "trending_zscore"}

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def insert_batch(self, records: list[ScoreRecord]) -> int:
        """Bulk-insert score records with ON CONFLICT DO UPDATE."""
        if not records:
            return 0

        async with self._session_factory() as session:
            values = [
                {
                    "person_id": r.person_id,
                    "date": r.date,
                    "window": r.window,
                    "popularity": r.popularity,
                    "trending_zscore": r.trending_zscore,
                }
                for r in records
            ]

            stmt = pg_insert(models.ScoreDaily).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["person_id", "date", "window"],
                set_={
                    "popularity": stmt.excluded.popularity,
                    "trending_zscore": stmt.excluded.trending_zscore,
                },
            )
            await session.execute(stmt)
            await session.commit()
            return len(records)

    async def get_ranked(
        self,
        window: str,
        score_date: datetime.date,
        score_column: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScoreRecord]:
        """Get top-scoring persons ranked by a score column."""
        if score_column not in self._SORTABLE_COLUMNS:
            raise ValueError(f"Invalid score_column: {score_column}. Must be one of {self._SORTABLE_COLUMNS}")

        sort_col = getattr(models.ScoreDaily, score_column)

        async with self._session_factory() as session:
            stmt = (
                select(models.ScoreDaily)
                .where(
                    models.ScoreDaily.window == window,
                    models.ScoreDaily.date == score_date,
                )
                .order_by(sort_col.desc().nulls_last())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return [_row_to_domain(r) for r in result.scalars().all()]

    async def get_by_person_and_date_range(
        self,
        person_id: str,
        window: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[ScoreRecord]:
        """Get score records for a person within a date range."""
        async with self._session_factory() as session:
            stmt = (
                select(models.ScoreDaily)
                .where(
                    models.ScoreDaily.person_id == person_id,
                    models.ScoreDaily.window == window,
                    models.ScoreDaily.date >= start_date,
                    models.ScoreDaily.date <= end_date,
                )
                .order_by(models.ScoreDaily.date)
            )
            result = await session.execute(stmt)
            return [_row_to_domain(r) for r in result.scalars().all()]


def _row_to_domain(row: models.ScoreDaily) -> ScoreRecord:
    """Convert a SQLAlchemy model to a domain ScoreRecord."""
    return ScoreRecord(
        person_id=row.person_id,
        date=row.date,
        window=row.window,
        popularity=row.popularity or 0,
        trending_zscore=row.trending_zscore,
    )
