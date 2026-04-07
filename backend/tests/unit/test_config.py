"""Tests for the configuration module."""

from pathlib import Path

import pytest
import yaml

from poi_people.infrastructure.config.loader import load_config
from poi_people.infrastructure.config.models import AppConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_yaml(tmp_path: Path) -> Path:
    """Write a minimal valid config YAML and return its path."""
    config = {
        "language_editions": ["en", "ja", "ru", "de", "es", "fr", "zh", "it", "pt", "pl"],
        "person_categories": {
            "Q82955": "politician",
            "Q193391": "politician",
            "Q2066131": "athlete",
            "Q937857": "athlete",
            "Q33999": "artist",
            "Q177220": "artist",
            "Q901": "scientist",
            "Q43845": "business",
            "Q36180": "writer",
        },
        "pipeline": {
            "retry_max_attempts": 3,
            "retry_backoff_minutes": [1, 5, 15],
            "wikimedia_user_agent": "PeopleOfInterest/0.1 (test@example.com)",
            "wikimedia_rate_limit_rps": 1,
        },
        "s3_bucket": "poi-pageview-dumps",
    }
    path = tmp_path / "settings.yaml"
    path.write_text(yaml.dump(config, default_flow_style=False))
    return path


@pytest.fixture
def valid_config(valid_yaml: Path) -> AppConfig:
    """Load and return a valid AppConfig from the fixture YAML."""
    return load_config(valid_yaml)


# ---------------------------------------------------------------------------
# Happy path tests
# ---------------------------------------------------------------------------


class TestLoadConfig:
    """Test loading and parsing of the YAML config into typed objects."""

    def test_returns_app_config(self, valid_config: AppConfig) -> None:
        assert isinstance(valid_config, AppConfig)

    def test_language_editions_loaded(self, valid_config: AppConfig) -> None:
        assert valid_config.language_editions == [
            "en", "ja", "ru", "de", "es", "fr", "zh", "it", "pt", "pl"
        ]

    def test_language_editions_count(self, valid_config: AppConfig) -> None:
        assert len(valid_config.language_editions) == 10

    def test_s3_bucket(self, valid_config: AppConfig) -> None:
        assert valid_config.s3_bucket == "poi-pageview-dumps"


class TestPersonCategoryMapping:
    """Test P106 person category mapping."""

    def test_politician_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q82955") == "politician"
        assert mapping.resolve("Q193391") == "politician"

    def test_athlete_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q2066131") == "athlete"
        assert mapping.resolve("Q937857") == "athlete"

    def test_artist_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q33999") == "artist"
        assert mapping.resolve("Q177220") == "artist"

    def test_scientist_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q901") == "scientist"

    def test_business_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q43845") == "business"

    def test_writer_mapping(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q36180") == "writer"

    def test_unknown_qid_returns_other(self, valid_config: AppConfig) -> None:
        mapping = valid_config.person_categories
        assert mapping.resolve("Q99999999") == "other"


class TestPipelineSettings:
    """Test pipeline configuration."""

    def test_retry_max_attempts(self, valid_config: AppConfig) -> None:
        assert valid_config.pipeline.retry_max_attempts == 3

    def test_retry_backoff(self, valid_config: AppConfig) -> None:
        assert valid_config.pipeline.retry_backoff_minutes == [1, 5, 15]

    def test_user_agent(self, valid_config: AppConfig) -> None:
        assert "PeopleOfInterest" in valid_config.pipeline.wikimedia_user_agent

    def test_rate_limit(self, valid_config: AppConfig) -> None:
        assert valid_config.pipeline.wikimedia_rate_limit_rps == 1


# ---------------------------------------------------------------------------
# Validation / error tests
# ---------------------------------------------------------------------------


class TestConfigValidationErrors:
    """Test that invalid configs raise clear errors."""

    def test_missing_file_raises_error(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_empty_language_editions_raises_error(self, tmp_path: Path) -> None:
        config = {
            "language_editions": [],
            "person_categories": {"Q82955": "politician"},
            "pipeline": {
                "retry_max_attempts": 3,
                "retry_backoff_minutes": [1, 5, 15],
                "wikimedia_user_agent": "Test/0.1",
                "wikimedia_rate_limit_rps": 1,
            },
            "s3_bucket": "test",
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(config))
        with pytest.raises(ValueError, match="language_editions"):
            load_config(path)

    def test_missing_person_categories_raises_error(self, tmp_path: Path) -> None:
        config = {
            "language_editions": ["en"],
            "pipeline": {
                "retry_max_attempts": 3,
                "retry_backoff_minutes": [1, 5, 15],
                "wikimedia_user_agent": "Test/0.1",
                "wikimedia_rate_limit_rps": 1,
            },
            "s3_bucket": "test",
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(config))
        with pytest.raises(ValueError):
            load_config(path)

    def test_invalid_category_in_mapping_raises_error(self, tmp_path: Path) -> None:
        config = {
            "language_editions": ["en"],
            "person_categories": {"Q82955": "invalid_category"},
            "pipeline": {
                "retry_max_attempts": 3,
                "retry_backoff_minutes": [1, 5, 15],
                "wikimedia_user_agent": "Test/0.1",
                "wikimedia_rate_limit_rps": 1,
            },
            "s3_bucket": "test",
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(config))
        with pytest.raises(ValueError, match="category"):
            load_config(path)

    def test_invalid_yaml_syntax_raises_error(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.yaml"
        path.write_text("{ invalid yaml: [")
        with pytest.raises(ValueError, match="[Pp]arse|[Yy]AML|syntax"):
            load_config(path)

    def test_negative_retry_attempts_raises_error(self, tmp_path: Path) -> None:
        config = {
            "language_editions": ["en"],
            "person_categories": {"Q82955": "politician"},
            "pipeline": {
                "retry_max_attempts": -1,
                "retry_backoff_minutes": [1, 5, 15],
                "wikimedia_user_agent": "Test/0.1",
                "wikimedia_rate_limit_rps": 1,
            },
            "s3_bucket": "test",
        }
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.dump(config))
        with pytest.raises(ValueError):
            load_config(path)


class TestDefaultConfig:
    """Test loading the actual project settings.yaml file."""

    def test_load_project_config(self) -> None:
        """Ensure the shipped settings.yaml is valid and loadable."""
        settings_path = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"
        if not settings_path.exists():
            pytest.skip("settings.yaml not yet created")
        config = load_config(settings_path)
        assert isinstance(config, AppConfig)
        assert len(config.language_editions) >= 10
