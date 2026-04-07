"""PageviewRepository protocol — persistence port for PageviewRecord."""

from __future__ import annotations

import datetime
from typing import Protocol, runtime_checkable

from poi_people.domain.entities.pageview_record import PageviewRecord


@runtime_checkable
class PageviewRepository(Protocol):
    """Repository interface for PageviewRecord persistence.

    Implementations handle the actual database operations.
    The domain layer depends only on this protocol.
    """

    async def insert_batch(self, records: list[PageviewRecord]) -> int:
        """Bulk-insert pageview records.

        Args:
            records: List of PageviewRecord objects to insert.

        Returns:
            Number of records inserted.
        """
        ...

    async def get_by_person_and_date_range(
        self, person_id: str, start_date: datetime.date, end_date: datetime.date
    ) -> list[PageviewRecord]:
        """Get all pageview records for a person within a date range.

        Args:
            person_id: Wikidata ID of the person.
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).

        Returns:
            List of PageviewRecord objects.
        """
        ...

    async def get_by_person_lang_and_date_range(
        self,
        person_id: str,
        lang: str,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> list[PageviewRecord]:
        """Get pageview records for a person and language within a date range.

        Args:
            person_id: Wikidata ID of the person.
            lang: Language edition code.
            start_date: Start of the date range (inclusive).
            end_date: End of the date range (inclusive).

        Returns:
            List of PageviewRecord objects.
        """
        ...
