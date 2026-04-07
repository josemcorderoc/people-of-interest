"""PageviewRecord domain model — a daily pageview count for one person+language."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, field_validator


class PageviewRecord(BaseModel, frozen=True):
    """A single day's pageview count for a person in a specific language edition.

    Attributes:
        person_id: Wikidata ID of the person.
        lang: Language edition code (e.g. "en", "fr").
        date: The date the pageviews were recorded.
        views: Raw pageview count (must be >= 0).
    """

    person_id: str
    lang: str
    date: datetime.date
    views: int

    @field_validator("person_id")
    @classmethod
    def person_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("person_id must not be empty")
        return v

    @field_validator("lang")
    @classmethod
    def lang_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("lang must not be empty")
        return v

    @field_validator("views")
    @classmethod
    def views_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("views must be non-negative")
        return v
