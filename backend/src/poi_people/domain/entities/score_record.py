"""ScoreRecord domain model — pre-computed popularity/trending scores."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

Window = Literal["daily", "weekly", "monthly"]


class ScoreRecord(BaseModel, frozen=True):
    """Pre-computed score for a person on a given date and time window.

    Attributes:
        person_id: Wikidata ID of the person.
        date: The date the score was computed for.
        window: Time window — daily, weekly, or monthly.
        popularity: Total views across all languages for the window.
        trending_zscore: Z-score over 30-day rolling mean.
    """

    person_id: str
    date: datetime.date
    window: Window
    popularity: int
    trending_zscore: float | None = None

    @field_validator("person_id")
    @classmethod
    def person_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("person_id must not be empty")
        return v

    @field_validator("popularity")
    @classmethod
    def popularity_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("popularity must be non-negative")
        return v
