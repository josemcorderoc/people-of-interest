"""PipelineRun domain model — tracks pipeline execution state."""

from __future__ import annotations

import datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator

Stage = Literal["person_sync", "pageview_ingest", "score_compute"]
Status = Literal["running", "success", "failed"]


class PipelineRun(BaseModel, frozen=True):
    """A record of a pipeline execution run.

    Attributes:
        id: Auto-generated database ID (None before persistence).
        stage: Pipeline stage name.
        run_date: The date the pipeline run covers.
        status: Current status of the run.
        started_at: When the run started.
        finished_at: When the run finished (None if still running).
        record_count: Number of records processed.
        error_detail: Error message on failure (None on success).
        metadata: Additional structured data about the run.
    """

    id: int | None = None
    stage: Stage
    run_date: datetime.date
    status: Status
    started_at: datetime.datetime
    finished_at: datetime.datetime | None = None
    record_count: int = 0
    error_detail: str | None = None
    metadata: dict[str, Any] = {}

    @field_validator("record_count")
    @classmethod
    def record_count_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("record_count must be non-negative")
        return v
