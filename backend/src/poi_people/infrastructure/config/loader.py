"""Configuration loading and validation.

Loads YAML config files and parses them into typed Pydantic models.
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from poi_people.infrastructure.config.models import AppConfig


def load_config(path: Path) -> AppConfig:
    """Load and validate application configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A validated AppConfig instance.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the YAML is invalid or config values fail validation.
    """
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    raw_text = path.read_text(encoding="utf-8")

    try:
        raw = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        msg = f"Failed to parse YAML configuration: {exc}"
        raise ValueError(msg) from exc

    if not isinstance(raw, dict):
        msg = "Configuration must be a YAML mapping at the top level"
        raise ValueError(msg)

    # Validate required top-level keys
    required_keys = {"language_editions", "person_categories", "pipeline", "s3_bucket"}
    missing = required_keys - set(raw.keys())
    if missing:
        msg = f"Missing required configuration sections: {', '.join(sorted(missing))}"
        raise ValueError(msg)

    # Transform person_categories from flat dict to nested structure
    pc_raw = raw.get("person_categories", {})
    if isinstance(pc_raw, dict) and "p106_mapping" not in pc_raw:
        raw["person_categories"] = {"p106_mapping": pc_raw}

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        msg = f"Configuration validation failed:\n{exc}"
        raise ValueError(msg) from exc
