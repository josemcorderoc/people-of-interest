"""SQLAlchemy implementation of the PipelineLogRepository protocol."""

from __future__ import annotations

import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poi_people.domain.entities.pipeline_run import PipelineRun
from poi_people.infrastructure.database import models


class SqlPipelineLogRepository:
    """SQLAlchemy-backed PipelineLogRepository implementation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def insert(self, run: PipelineRun) -> int:
        """Insert a new pipeline run record and return its generated ID."""
        async with self._session_factory() as session:
            row = models.PipelineLog(
                stage=run.stage,
                run_date=run.run_date,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                record_count=run.record_count,
                error_detail=run.error_detail,
                metadata_=run.metadata,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return row.id

    async def update_status(
        self,
        run_id: int,
        status: str,
        finished_at: datetime.datetime | None = None,
        record_count: int | None = None,
        error_detail: str | None = None,
    ) -> None:
        """Update the status of an existing pipeline run."""
        async with self._session_factory() as session:
            values: dict = {"status": status}
            if finished_at is not None:
                values["finished_at"] = finished_at
            if record_count is not None:
                values["record_count"] = record_count
            if error_detail is not None:
                values["error_detail"] = error_detail

            stmt = update(models.PipelineLog).where(models.PipelineLog.id == run_id).values(**values)
            await session.execute(stmt)
            await session.commit()

    async def get_by_stage_and_date(
        self, stage: str, run_date: datetime.date
    ) -> list[PipelineRun]:
        """Get pipeline runs for a given stage and date."""
        async with self._session_factory() as session:
            stmt = (
                select(models.PipelineLog)
                .where(
                    models.PipelineLog.stage == stage,
                    models.PipelineLog.run_date == run_date,
                )
                .order_by(models.PipelineLog.started_at.desc())
            )
            result = await session.execute(stmt)
            return [_row_to_domain(r) for r in result.scalars().all()]


def _row_to_domain(row: models.PipelineLog) -> PipelineRun:
    """Convert a SQLAlchemy model to a domain PipelineRun."""
    return PipelineRun(
        id=row.id,
        stage=row.stage,
        run_date=row.run_date,
        status=row.status,
        started_at=row.started_at,
        finished_at=row.finished_at,
        record_count=row.record_count or 0,
        error_detail=row.error_detail,
        metadata=row.metadata_ or {},
    )
