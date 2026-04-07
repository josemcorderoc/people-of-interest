"""ScoreRepository protocol — persistence port for ScoreRecord."""

from __future__ import annotations

import datetime
from typing import Protocol, runtime_checkable

from poi_people.domain.entities.score_record import ScoreRecord


@runtime_checkable
class ScoreRepository(Protocol):
    """Repository interface for ScoreRecord persistence.

    Implementations handle the actual database operations.
    The domain layer depends only on this protocol.
    """

    async def insert_batch(self, records: list[ScoreRecord]) -> int:
        """Bulk-insert score records.

        Args:
            records: List of ScoreRecord objects to insert.

        Returns:
            Number of records inserted.
        """
        ...

    async def get_ranked(
        self,
        window: str,
        score_date: datetime.date,
        score_column: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScoreRecord]:
        """Get top-scoring persons ranked by a score column.

        Args:
            window: Time window (daily/weekly/monthly).
            score_date: The date to query scores for.
            score_column: Which score column to sort by.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of ScoreRecord objects ordered by score descending.
        """
        ...

    async def get_by_person_and_date_range(
        self,
        person_id: str,
        window: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[ScoreRecord]:
        """Get score records for a person within a date range.

        Args:
            person_id: Wikidata ID of the person.
            window: Time window (daily/weekly/monthly).
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).

        Returns:
            List of ScoreRecord objects.
        """
        ...
