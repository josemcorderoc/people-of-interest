"""Typed Pydantic models for application configuration."""

from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = frozenset({
    "politician", "athlete", "artist", "scientist", "business", "writer", "historical", "other",
})


class PersonCategoryMapping(BaseModel):
    """Maps Wikidata P106 occupation QIDs to person categories."""

    p106_mapping: dict[str, str]

    @field_validator("p106_mapping")
    @classmethod
    def validate_categories(cls, v: dict[str, str]) -> dict[str, str]:
        for qid, category in v.items():
            if category not in VALID_CATEGORIES:
                msg = (
                    f"Invalid category '{category}' for QID '{qid}'. "
                    f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
                )
                raise ValueError(msg)
        return v

    def resolve(self, qid: str) -> str:
        """Resolve a Wikidata P106 QID to a person category.

        Returns 'other' for unknown QIDs.
        """
        return self.p106_mapping.get(qid, "other")


class PipelineSettings(BaseModel):
    """Pipeline execution settings."""

    retry_max_attempts: int = Field(ge=0)
    retry_backoff_minutes: list[int]
    wikimedia_user_agent: str
    wikimedia_rate_limit_rps: int = Field(ge=1)


class AppConfig(BaseModel):
    """Root application configuration."""

    language_editions: list[str] = Field(min_length=1)
    person_categories: PersonCategoryMapping
    pipeline: PipelineSettings
    s3_bucket: str
