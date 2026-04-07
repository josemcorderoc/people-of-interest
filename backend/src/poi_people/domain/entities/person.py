"""Person domain model — a notable person from Wikidata."""

from __future__ import annotations

import datetime
from typing import Literal

from pydantic import BaseModel, field_validator

PersonCategory = Literal[
    "politician", "athlete", "artist", "scientist", "business", "writer", "historical", "other"
]
Gender = Literal["male", "female", "other", "unknown"]


class Person(BaseModel, frozen=True):
    """A notable person sourced from Wikidata.

    Attributes:
        wikidata_id: Permanent Wikidata identifier (e.g. "Q76").
        name: Display name (English label by default).
        names_by_lang: Localized names keyed by language code.
        article_titles: Wikipedia article titles keyed by language code.
        category: Classification derived from Wikidata P106 occupation.
        birth_date: Date of birth (P569), nullable.
        death_date: Date of death (P570), nullable for living people.
        nationality: Primary nationality (P27), nullable.
        occupations: Full list of occupations from P106.
        image_filename: Wikimedia Commons filename from P18, nullable.
        gender: Gender from P21.
    """

    wikidata_id: str
    name: str
    names_by_lang: dict[str, str]
    article_titles: dict[str, str]
    category: PersonCategory
    birth_date: datetime.date | None = None
    death_date: datetime.date | None = None
    nationality: str | None = None
    occupations: list[str] = []
    image_filename: str | None = None
    gender: Gender = "unknown"

    @field_validator("wikidata_id")
    @classmethod
    def wikidata_id_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("wikidata_id must not be empty")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("name must not be empty")
        return v
