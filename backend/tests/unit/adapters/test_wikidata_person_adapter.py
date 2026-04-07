"""Unit tests for the Wikidata person adapter."""

from __future__ import annotations

import datetime
import gzip
import json
from pathlib import Path

import pytest

from poi_people.infrastructure.adapters.wikidata_person_adapter import (
    parse_entity,
    stream_persons_from_dump,
)
from poi_people.infrastructure.config.models import PersonCategoryMapping

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"

LANGUAGES = ["en", "ja", "de", "es", "fr"]

CATEGORY_MAPPING = PersonCategoryMapping(
    p106_mapping={
        "Q82955": "politician",
        "Q937857": "athlete",
        "Q177220": "artist",
        "Q33999": "artist",
        "Q169470": "scientist",
        "Q593644": "scientist",
        "Q43845": "business",
        "Q131524": "business",
        "Q36180": "writer",
        "Q6625963": "writer",
    }
)


@pytest.fixture
def sample_entities() -> list[dict]:
    """Load sample entities from the fixture file."""
    fixture_path = FIXTURES_DIR / "wikidata_persons.json"
    with open(fixture_path) as f:
        return json.load(f)


class TestParseEntity:
    """Tests for individual entity parsing."""

    def test_parse_obama(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[0]  # Obama
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.wikidata_id == "Q76"
        assert person.name == "Barack Obama"
        assert person.category == "politician"
        assert person.gender == "male"
        assert person.birth_date == datetime.date(1961, 8, 4)
        assert person.image_filename == "President_Barack_Obama.jpg"
        assert "en" in person.article_titles
        assert person.article_titles["en"] == "Barack Obama"

    def test_parse_merkel(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[1]  # Merkel
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.wikidata_id == "Q567"
        assert person.gender == "female"
        assert person.category == "politician"

    def test_parse_messi_athlete(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[2]  # Messi
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.category == "athlete"
        assert person.image_filename == "Lionel_Messi_2023.jpg"

    def test_non_human_filtered_out(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[3]  # The Beatles (band, not human)
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is None

    def test_parse_business_person(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[4]  # Bill Gates
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.category == "business"

    def test_parse_scientist_with_death_date(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[5]  # Einstein
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.category == "scientist"
        assert person.death_date == datetime.date(1955, 4, 18)

    def test_first_matching_occupation_wins(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[6]  # Taylor Swift (singer + writer)
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.category == "artist"  # singer (Q177220) mapped first

    def test_parse_writer(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[8]  # J.K. Rowling
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert person.category == "writer"

    def test_entity_without_birth_date_filtered(self) -> None:
        entity = {
            "type": "item",
            "id": "Q999",
            "labels": {"en": {"value": "No Birth"}},
            "sitelinks": {"enwiki": {"title": "No Birth"}},
            "claims": {
                "P31": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "numeric-id": 5}}}}],
            },
        }
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is None

    def test_entity_without_sitelinks_filtered(self) -> None:
        entity = {
            "type": "item",
            "id": "Q998",
            "labels": {"en": {"value": "No Sitelinks"}},
            "sitelinks": {},
            "claims": {
                "P31": [{"mainsnak": {"datavalue": {"value": {"entity-type": "item", "numeric-id": 5}}}}],
                "P569": [{"mainsnak": {"datavalue": {"value": {"time": "+1990-01-01T00:00:00Z"}}}}],
            },
        }
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is None

    def test_names_by_lang_populated(self, sample_entities: list[dict]) -> None:
        entity = sample_entities[0]  # Obama
        person = parse_entity(entity, LANGUAGES, CATEGORY_MAPPING)
        assert person is not None
        assert "en" in person.names_by_lang
        assert "ja" in person.names_by_lang
        assert person.names_by_lang["ja"] == "バラク・オバマ"


class TestStreamFromDump:
    """Tests for streaming from a gzipped dump file."""

    def test_stream_from_gzipped_fixture(self, tmp_path: Path, sample_entities: list[dict]) -> None:
        # Create a gzipped JSON dump
        dump_path = tmp_path / "test_dump.json.gz"
        json_lines = "[\n" + ",\n".join(json.dumps(e) for e in sample_entities) + "\n]"
        with gzip.open(dump_path, "wt", encoding="utf-8") as f:
            f.write(json_lines)

        persons = list(stream_persons_from_dump(dump_path, LANGUAGES, CATEGORY_MAPPING))

        # The Beatles (non-human) should be filtered out, 9 humans remain
        assert len(persons) == 9

        ids = {p.wikidata_id for p in persons}
        assert "Q76" in ids  # Obama
        assert "Q1299" not in ids  # Beatles filtered

    def test_empty_dump(self, tmp_path: Path) -> None:
        dump_path = tmp_path / "empty.json.gz"
        with gzip.open(dump_path, "wt", encoding="utf-8") as f:
            f.write("[\n]\n")

        persons = list(stream_persons_from_dump(dump_path, LANGUAGES, CATEGORY_MAPPING))
        assert len(persons) == 0
