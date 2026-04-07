"""Unit tests for domain entities, protocols, and repository interfaces."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, date, datetime

import pytest


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------
class TestPerson:
    """Tests for the Person domain model."""

    def test_create_minimal(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q76",
            name="Barack Obama",
            names_by_lang={"en": "Barack Obama", "ja": "バラク・オバマ"},
            article_titles={"en": "Barack Obama", "ja": "バラク・オバマ"},
            category="politician",
        )
        assert person.wikidata_id == "Q76"
        assert person.name == "Barack Obama"
        assert person.category == "politician"

    def test_create_full(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q76",
            name="Barack Obama",
            names_by_lang={"en": "Barack Obama"},
            article_titles={"en": "Barack Obama"},
            category="politician",
            birth_date=date(1961, 8, 4),
            death_date=None,
            nationality="American",
            occupations=["politician", "lawyer", "author"],
            image_filename="Barack_Obama.jpg",
            gender="male",
        )
        assert person.birth_date == date(1961, 8, 4)
        assert person.death_date is None
        assert person.nationality == "American"
        assert person.occupations == ["politician", "lawyer", "author"]
        assert person.image_filename == "Barack_Obama.jpg"
        assert person.gender == "male"

    def test_wikidata_id_required(self):
        from poi_people.domain.entities.person import Person

        with pytest.raises(Exception):
            Person(
                wikidata_id="",
                name="Test",
                names_by_lang={},
                article_titles={},
                category="other",
            )

    def test_name_required(self):
        from poi_people.domain.entities.person import Person

        with pytest.raises(Exception):
            Person(
                wikidata_id="Q1",
                name="",
                names_by_lang={},
                article_titles={},
                category="other",
            )

    def test_valid_categories(self):
        from poi_people.domain.entities.person import Person

        valid_cats = ["politician", "athlete", "artist", "scientist", "business", "writer", "historical", "other"]
        for cat in valid_cats:
            person = Person(
                wikidata_id="Q1",
                name="Test",
                names_by_lang={"en": "Test"},
                article_titles={"en": "Test"},
                category=cat,
            )
            assert person.category == cat

    def test_invalid_category(self):
        from poi_people.domain.entities.person import Person

        with pytest.raises(Exception):
            Person(
                wikidata_id="Q1",
                name="Test",
                names_by_lang={"en": "Test"},
                article_titles={"en": "Test"},
                category="invalid_type",
            )

    def test_valid_genders(self):
        from poi_people.domain.entities.person import Person

        for gender in ["male", "female", "other", "unknown"]:
            person = Person(
                wikidata_id="Q1",
                name="Test",
                names_by_lang={"en": "Test"},
                article_titles={"en": "Test"},
                category="other",
                gender=gender,
            )
            assert person.gender == gender

    def test_defaults(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q1",
            name="Test",
            names_by_lang={},
            article_titles={},
            category="other",
        )
        assert person.birth_date is None
        assert person.death_date is None
        assert person.nationality is None
        assert person.occupations == []
        assert person.image_filename is None
        assert person.gender == "unknown"

    def test_serialization_roundtrip(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q76",
            name="Barack Obama",
            names_by_lang={"en": "Barack Obama"},
            article_titles={"en": "Barack Obama"},
            category="politician",
            birth_date=date(1961, 8, 4),
            gender="male",
        )
        data = person.model_dump()
        restored = Person.model_validate(data)
        assert restored == person

    def test_json_serialization(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q76",
            name="Barack Obama",
            names_by_lang={"en": "Barack Obama"},
            article_titles={"en": "Barack Obama"},
            category="politician",
        )
        json_str = person.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["wikidata_id"] == "Q76"

    def test_immutability(self):
        from poi_people.domain.entities.person import Person

        person = Person(
            wikidata_id="Q76",
            name="Barack Obama",
            names_by_lang={"en": "Barack Obama"},
            article_titles={"en": "Barack Obama"},
            category="politician",
        )
        with pytest.raises(Exception):
            person.name = "Test"


# ---------------------------------------------------------------------------
# PageviewRecord
# ---------------------------------------------------------------------------
class TestPageviewRecord:
    """Tests for the PageviewRecord domain model."""

    def test_create(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        record = PageviewRecord(
            person_id="Q76",
            lang="en",
            date=date(2026, 4, 1),
            views=12345,
        )
        assert record.person_id == "Q76"
        assert record.lang == "en"
        assert record.date == date(2026, 4, 1)
        assert record.views == 12345

    def test_views_must_be_non_negative(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        with pytest.raises(Exception):
            PageviewRecord(person_id="Q76", lang="en", date=date(2026, 4, 1), views=-1)

    def test_person_id_required(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        with pytest.raises(Exception):
            PageviewRecord(person_id="", lang="en", date=date(2026, 4, 1), views=100)

    def test_lang_required(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        with pytest.raises(Exception):
            PageviewRecord(person_id="Q76", lang="", date=date(2026, 4, 1), views=100)

    def test_serialization_roundtrip(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        record = PageviewRecord(person_id="Q76", lang="en", date=date(2026, 4, 1), views=100)
        data = record.model_dump()
        restored = PageviewRecord.model_validate(data)
        assert restored == record

    def test_immutability(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        record = PageviewRecord(person_id="Q76", lang="en", date=date(2026, 4, 1), views=100)
        with pytest.raises(Exception):
            record.views = 200


# ---------------------------------------------------------------------------
# ScoreRecord
# ---------------------------------------------------------------------------
class TestScoreRecord:
    """Tests for the ScoreRecord domain model."""

    def test_create_full(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        record = ScoreRecord(
            person_id="Q76",
            date=date(2026, 4, 1),
            window="daily",
            popularity=50000,
            trending_zscore=2.5,
        )
        assert record.person_id == "Q76"
        assert record.date == date(2026, 4, 1)
        assert record.window == "daily"
        assert record.popularity == 50000
        assert record.trending_zscore == 2.5

    def test_nullable_trending_fields(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        record = ScoreRecord(
            person_id="Q76", date=date(2026, 4, 1), window="daily", popularity=50000, trending_zscore=None
        )
        assert record.trending_zscore is None

    def test_valid_windows(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        for window in ["daily", "weekly", "monthly"]:
            record = ScoreRecord(person_id="Q76", date=date(2026, 4, 1), window=window, popularity=100)
            assert record.window == window

    def test_person_id_required(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        with pytest.raises(Exception):
            ScoreRecord(person_id="", date=date(2026, 4, 1), window="daily", popularity=100)

    def test_invalid_window(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        with pytest.raises(Exception):
            ScoreRecord(person_id="Q76", date=date(2026, 4, 1), window="hourly", popularity=100)

    def test_popularity_must_be_non_negative(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        with pytest.raises(Exception):
            ScoreRecord(person_id="Q76", date=date(2026, 4, 1), window="daily", popularity=-1)

    def test_defaults_for_optional_fields(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        record = ScoreRecord(person_id="Q76", date=date(2026, 4, 1), window="daily", popularity=100)
        assert record.trending_zscore is None

    def test_serialization_roundtrip(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        record = ScoreRecord(
            person_id="Q76", date=date(2026, 4, 1), window="weekly", popularity=50000, trending_zscore=2.5
        )
        data = record.model_dump()
        restored = ScoreRecord.model_validate(data)
        assert restored == record

    def test_immutability(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        record = ScoreRecord(person_id="Q76", date=date(2026, 4, 1), window="daily", popularity=100)
        with pytest.raises(Exception):
            record.popularity = 200


# ---------------------------------------------------------------------------
# PipelineRun
# ---------------------------------------------------------------------------
class TestPipelineRun:
    """Tests for the PipelineRun domain model."""

    def test_create_full(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="person_sync",
            run_date=date(2026, 4, 1),
            status="success",
            started_at=now,
            finished_at=now,
            record_count=1000,
            error_detail=None,
            metadata={"persons_processed": 1000},
        )
        assert run.stage == "person_sync"
        assert run.run_date == date(2026, 4, 1)
        assert run.status == "success"
        assert run.record_count == 1000

    def test_valid_stages(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        for stage in ["person_sync", "pageview_ingest", "score_compute"]:
            run = PipelineRun(stage=stage, run_date=date(2026, 4, 1), status="running", started_at=now)
            assert run.stage == stage

    def test_invalid_stage(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        with pytest.raises(Exception):
            PipelineRun(
                stage="invalid_stage", run_date=date(2026, 4, 1),
                status="running", started_at=now,
            )

    def test_valid_statuses(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        for status in ["running", "success", "failed"]:
            run = PipelineRun(
                stage="person_sync", run_date=date(2026, 4, 1),
                status=status, started_at=now,
            )
            assert run.status == status

    def test_invalid_status(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        with pytest.raises(Exception):
            PipelineRun(
                stage="person_sync", run_date=date(2026, 4, 1),
                status="cancelled", started_at=now,
            )

    def test_finished_at_optional(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="person_sync", run_date=date(2026, 4, 1),
            status="running", started_at=now,
        )
        assert run.finished_at is None

    def test_record_count_defaults_to_zero(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="person_sync", run_date=date(2026, 4, 1),
            status="running", started_at=now,
        )
        assert run.record_count == 0

    def test_metadata_defaults_to_empty_dict(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="person_sync", run_date=date(2026, 4, 1),
            status="running", started_at=now,
        )
        assert run.metadata == {}

    def test_record_count_non_negative(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        with pytest.raises(Exception):
            PipelineRun(
                stage="person_sync", run_date=date(2026, 4, 1),
                status="running", started_at=datetime.now(UTC),
                record_count=-1,
            )

    def test_serialization_roundtrip(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="pageview_ingest", run_date=date(2026, 4, 1),
            status="failed", started_at=now, finished_at=now,
            record_count=0, error_detail="Connection timeout",
            metadata={"attempt": 3},
        )
        data = run.model_dump()
        restored = PipelineRun.model_validate(data)
        assert restored == run

    def test_immutability(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        now = datetime.now(UTC)
        run = PipelineRun(
            stage="person_sync", run_date=date(2026, 4, 1),
            status="running", started_at=now,
        )
        with pytest.raises(Exception):
            run.status = "success"


# ---------------------------------------------------------------------------
# SourceConfig
# ---------------------------------------------------------------------------
class TestSourceConfig:
    """Tests for the SourceConfig value object."""

    def test_create(self):
        from poi_people.domain.services.source_adapter import SourceConfig

        config = SourceConfig(
            languages=["en", "fr", "de"],
            user_agent="PeopleOfInterest/0.1 (test@example.com)",
        )
        assert config.languages == ["en", "fr", "de"]
        assert config.user_agent == "PeopleOfInterest/0.1 (test@example.com)"

    def test_languages_required(self):
        from poi_people.domain.services.source_adapter import SourceConfig

        with pytest.raises(Exception):
            SourceConfig(languages=[], user_agent="PeopleOfInterest/0.1 (test@example.com)")

    def test_user_agent_required(self):
        from poi_people.domain.services.source_adapter import SourceConfig

        with pytest.raises(Exception):
            SourceConfig(languages=["en"], user_agent="")


# ---------------------------------------------------------------------------
# SourceAdapter Protocol
# ---------------------------------------------------------------------------
class TestSourceAdapterProtocol:
    """Tests that the SourceAdapter protocol is properly defined."""

    def test_protocol_defines_fetch_persons(self):
        from poi_people.domain.services.source_adapter import SourceAdapter

        assert hasattr(SourceAdapter, "fetch_persons")

    def test_protocol_defines_fetch_pageviews(self):
        from poi_people.domain.services.source_adapter import SourceAdapter

        assert hasattr(SourceAdapter, "fetch_pageviews")

    def test_concrete_class_satisfies_protocol(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord
        from poi_people.domain.entities.person import Person
        from poi_people.domain.services.source_adapter import SourceAdapter, SourceConfig

        class FakeAdapter:
            def fetch_persons(self, config: SourceConfig) -> Iterator[Person]:
                yield Person(
                    wikidata_id="Q1",
                    name="Test",
                    names_by_lang={"en": "Test"},
                    article_titles={"en": "Test"},
                    category="other",
                )

            def fetch_pageviews(
                self, date: date, lang: str, config: SourceConfig
            ) -> Iterator[PageviewRecord]:
                yield PageviewRecord(person_id="Q1", lang="en", date=date, views=100)

        adapter = FakeAdapter()
        assert isinstance(adapter, SourceAdapter)


# ---------------------------------------------------------------------------
# Repository Protocols
# ---------------------------------------------------------------------------
class TestPersonRepository:
    """Tests for the PersonRepository protocol."""

    def test_protocol_defines_methods(self):
        from poi_people.domain.repositories.person_repository import PersonRepository

        assert hasattr(PersonRepository, "upsert_batch")
        assert hasattr(PersonRepository, "get_by_id")
        assert hasattr(PersonRepository, "search_by_text")

    def test_concrete_class_satisfies_protocol(self):
        from poi_people.domain.entities.person import Person
        from poi_people.domain.repositories.person_repository import PersonRepository

        class FakePersonRepo:
            async def upsert_batch(self, persons: list[Person]) -> int:
                return len(persons)

            async def get_by_id(self, wikidata_id: str) -> Person | None:
                return None

            async def search_by_text(self, query: str, limit: int = 20) -> list[Person]:
                return []

            async def get_article_title_mapping(self, lang: str) -> dict[str, str]:
                return {}

        repo = FakePersonRepo()
        assert isinstance(repo, PersonRepository)


class TestPageviewRepository:
    """Tests for the PageviewRepository protocol."""

    def test_protocol_defines_methods(self):
        from poi_people.domain.repositories.pageview_repository import PageviewRepository

        assert hasattr(PageviewRepository, "insert_batch")
        assert hasattr(PageviewRepository, "get_by_person_and_date_range")
        assert hasattr(PageviewRepository, "get_by_person_lang_and_date_range")

    def test_concrete_class_satisfies_protocol(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord
        from poi_people.domain.repositories.pageview_repository import PageviewRepository

        class FakePageviewRepo:
            async def insert_batch(self, records: list[PageviewRecord]) -> int:
                return len(records)

            async def get_by_person_and_date_range(
                self, person_id: str, start_date: date, end_date: date
            ) -> list[PageviewRecord]:
                return []

            async def get_by_person_lang_and_date_range(
                self, person_id: str, lang: str, start_date: date, end_date: date
            ) -> list[PageviewRecord]:
                return []

        repo = FakePageviewRepo()
        assert isinstance(repo, PageviewRepository)


class TestScoreRepository:
    """Tests for the ScoreRepository protocol."""

    def test_protocol_defines_methods(self):
        from poi_people.domain.repositories.score_repository import ScoreRepository

        assert hasattr(ScoreRepository, "insert_batch")
        assert hasattr(ScoreRepository, "get_ranked")
        assert hasattr(ScoreRepository, "get_by_person_and_date_range")

    def test_concrete_class_satisfies_protocol(self):
        from poi_people.domain.entities.score_record import ScoreRecord
        from poi_people.domain.repositories.score_repository import ScoreRepository

        class FakeScoreRepo:
            async def insert_batch(self, records: list[ScoreRecord]) -> int:
                return len(records)

            async def get_ranked(
                self, window: str, score_date: date, score_column: str, limit: int = 50, offset: int = 0
            ) -> list[ScoreRecord]:
                return []

            async def get_by_person_and_date_range(
                self, person_id: str, window: str, start_date: date, end_date: date
            ) -> list[ScoreRecord]:
                return []

        repo = FakeScoreRepo()
        assert isinstance(repo, ScoreRepository)


class TestPipelineLogRepository:
    """Tests for the PipelineLogRepository protocol."""

    def test_protocol_defines_methods(self):
        from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository

        assert hasattr(PipelineLogRepository, "insert")
        assert hasattr(PipelineLogRepository, "update_status")
        assert hasattr(PipelineLogRepository, "get_by_stage_and_date")

    def test_concrete_class_satisfies_protocol(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun
        from poi_people.domain.repositories.pipeline_log_repository import PipelineLogRepository

        class FakePipelineLogRepo:
            async def insert(self, run: PipelineRun) -> int:
                return 1

            async def update_status(
                self, run_id: int, status: str, finished_at: datetime | None = None,
                record_count: int | None = None, error_detail: str | None = None,
            ) -> None:
                pass

            async def get_by_stage_and_date(self, stage: str, run_date: date) -> list[PipelineRun]:
                return []

        repo = FakePipelineLogRepo()
        assert isinstance(repo, PipelineLogRepository)


# ---------------------------------------------------------------------------
# Domain module imports
# ---------------------------------------------------------------------------
class TestDomainImports:
    """Verify all domain models are importable from the entities package."""

    def test_import_person(self):
        from poi_people.domain.entities.person import Person

        assert Person is not None

    def test_import_pageview_record(self):
        from poi_people.domain.entities.pageview_record import PageviewRecord

        assert PageviewRecord is not None

    def test_import_score_record(self):
        from poi_people.domain.entities.score_record import ScoreRecord

        assert ScoreRecord is not None

    def test_import_pipeline_run(self):
        from poi_people.domain.entities.pipeline_run import PipelineRun

        assert PipelineRun is not None

    def test_import_source_adapter(self):
        from poi_people.domain.services.source_adapter import SourceAdapter, SourceConfig

        assert SourceAdapter is not None
        assert SourceConfig is not None

    def test_import_from_entities_package(self):
        """All models should be importable from the entities package __init__."""
        from poi_people.domain.entities import PageviewRecord, Person, PipelineRun, ScoreRecord

        assert Person is not None
        assert PageviewRecord is not None
        assert ScoreRecord is not None
        assert PipelineRun is not None

    def test_no_infrastructure_imports(self):
        """Domain layer must not depend on infrastructure (DB, HTTP, etc.)."""
        import importlib

        modules_to_check = [
            "poi_people.domain.entities.person",
            "poi_people.domain.entities.pageview_record",
            "poi_people.domain.entities.score_record",
            "poi_people.domain.entities.pipeline_run",
            "poi_people.domain.services.source_adapter",
            "poi_people.domain.repositories.person_repository",
            "poi_people.domain.repositories.pageview_repository",
            "poi_people.domain.repositories.score_repository",
            "poi_people.domain.repositories.pipeline_log_repository",
        ]

        forbidden_prefixes = [
            "sqlalchemy", "asyncpg", "psycopg", "httpx",
            "requests", "aiohttp", "fastapi", "uvicorn", "alembic",
        ]

        for mod_name in modules_to_check:
            mod = importlib.import_module(mod_name)
            source_file = getattr(mod, "__file__", "")
            if source_file:
                with open(source_file) as f:
                    source = f.read()
                for prefix in forbidden_prefixes:
                    assert f"import {prefix}" not in source, (
                        f"Domain module {mod_name} imports forbidden package '{prefix}'"
                    )
                    assert f"from {prefix}" not in source, (
                        f"Domain module {mod_name} imports forbidden package '{prefix}'"
                    )
