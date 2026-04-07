"""SQLAlchemy implementation of the PageviewRepository protocol."""

from __future__ import annotations

import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poi_people.domain.entities.pageview_record import PageviewRecord
from poi_people.infrastructure.database import models


class SqlPageviewRepository:
    """SQLAlchemy-backed PageviewRepository implementation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def insert_batch(self, records: list[PageviewRecord]) -> int:
        """Bulk-insert pageview records with ON CONFLICT DO UPDATE (sum views)."""
        if not records:
            return 0

        async with self._session_factory() as session:
            values = [
                {
                    "person_id": r.person_id,
                    "lang": r.lang,
                    "date": r.date,
                    "views": r.views,
                }
                for r in records
            ]

            stmt = pg_insert(models.PageviewDaily).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["person_id", "lang", "date"],
                set_={"views": stmt.excluded.views},
            )
            await session.execute(stmt)
            await session.commit()
            return len(records)

    async def get_by_person_and_date_range(
        self, person_id: str, start_date: datetime.date, end_date: datetime.date
    ) -> list[PageviewRecord]:
        """Get all pageview records for a person within a date range."""
        async with self._session_factory() as session:
            stmt = (
                select(models.PageviewDaily)
                .where(
                    models.PageviewDaily.person_id == person_id,
                    models.PageviewDaily.date >= start_date,
                    models.PageviewDaily.date <= end_date,
                )
                .order_by(models.PageviewDaily.date)
            )
            result = await session.execute(stmt)
            return [_row_to_domain(r) for r in result.scalars().all()]

    async def get_by_person_lang_and_date_range(
        self,
        person_id: str,
        lang: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[PageviewRecord]:
        """Get pageview records for a person and language within a date range."""
        async with self._session_factory() as session:
            stmt = (
                select(models.PageviewDaily)
                .where(
                    models.PageviewDaily.person_id == person_id,
                    models.PageviewDaily.lang == lang,
                    models.PageviewDaily.date >= start_date,
                    models.PageviewDaily.date <= end_date,
                )
                .order_by(models.PageviewDaily.date)
            )
            result = await session.execute(stmt)
            return [_row_to_domain(r) for r in result.scalars().all()]


def _row_to_domain(row: models.PageviewDaily) -> PageviewRecord:
    """Convert a SQLAlchemy model to a domain PageviewRecord."""
    return PageviewRecord(
        person_id=row.person_id,
        lang=row.lang,
        date=row.date,
        views=row.views,
    )
