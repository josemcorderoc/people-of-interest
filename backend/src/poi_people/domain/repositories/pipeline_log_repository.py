"""PipelineLogRepository protocol — persistence port for PipelineRun."""

from __future__ import annotations

import datetime
from typing import Protocol, runtime_checkable

from poi_people.domain.entities.pipeline_run import PipelineRun


@runtime_checkable
class PipelineLogRepository(Protocol):
    """Repository interface for PipelineRun persistence.

    Implementations handle the actual database operations.
    The domain layer depends only on this protocol.
    """

    async def insert(self, run: PipelineRun) -> int:
        """Insert a new pipeline run record.

        Args:
            run: PipelineRun domain object.

        Returns:
            The auto-generated ID of the inserted record.
        """
        ...

    async def update_status(
        self,
        run_id: int,
        status: str,
        finished_at: datetime.datetime | None = None,
        record_count: int | None = None,
        error_detail: str | None = None,
    ) -> None:
        """Update the status of an existing pipeline run.

        Args:
            run_id: The ID of the run to update.
            status: New status value.
            finished_at: Completion timestamp.
            record_count: Number of records processed.
            error_detail: Error message (for failed runs).
        """
        ...

    async def get_by_stage_and_date(
        self, stage: str, run_date: datetime.date
    ) -> list[PipelineRun]:
        """Get pipeline runs for a given stage and date.

        Args:
            stage: Pipeline stage name.
            run_date: The date to query.

        Returns:
            List of PipelineRun objects.
        """
        ...
