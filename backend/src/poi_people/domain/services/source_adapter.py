"""SourceAdapter protocol — abstraction for data source access."""

from __future__ import annotations

import datetime
from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, field_validator

from poi_people.domain.entities.pageview_record import PageviewRecord
from poi_people.domain.entities.person import Person


class SourceConfig(BaseModel, frozen=True):
    """Configuration for a data source adapter.

    Attributes:
        languages: List of language edition codes to process.
        user_agent: Polite User-Agent string for HTTP requests.
    """

    languages: list[str]
    user_agent: str

    @field_validator("languages")
    @classmethod
    def languages_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("languages must not be empty")
        return v

    @field_validator("user_agent")
    @classmethod
    def user_agent_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("user_agent must not be empty")
        return v


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol for data source adapters (e.g. Wikidata).

    Implementations provide methods to fetch person data and pageview data
    from an external source. The adapter pattern isolates source-specific
    logic so new sources can be added without changing scoring or serving code.
    """

    def fetch_persons(self, config: SourceConfig) -> Iterator[Person]:
        """Stream persons from the data source.

        Args:
            config: Source configuration with language editions and user agent.

        Yields:
            Person domain objects.
        """
        ...

    def fetch_pageviews(
        self, date: datetime.date, lang: str, config: SourceConfig
    ) -> Iterator[PageviewRecord]:
        """Stream pageview records for a given date and language.

        Args:
            date: The date to fetch pageviews for.
            lang: Language edition code.
            config: Source configuration.

        Yields:
            PageviewRecord domain objects.
        """
        ...
