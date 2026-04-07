"""PersonRepository protocol — persistence port for Person."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from poi_people.domain.entities.person import Person


@runtime_checkable
class PersonRepository(Protocol):
    """Repository interface for Person persistence.

    Implementations handle the actual database operations.
    The domain layer depends only on this protocol.
    """

    async def upsert_batch(self, persons: list[Person]) -> int:
        """Insert or update a batch of persons.

        Args:
            persons: List of Person objects to upsert.

        Returns:
            Number of persons upserted.
        """
        ...

    async def get_by_id(self, wikidata_id: str) -> Person | None:
        """Retrieve a person by their Wikidata ID.

        Args:
            wikidata_id: The Wikidata identifier (e.g. "Q76").

        Returns:
            The Person if found, None otherwise.
        """
        ...

    async def search_by_text(self, query: str, limit: int = 20) -> list[Person]:
        """Search persons by name across all languages.

        Args:
            query: Search string.
            limit: Maximum number of results.

        Returns:
            List of matching Person objects.
        """
        ...

    async def get_article_title_mapping(self, lang: str) -> dict[str, str]:
        """Get a mapping of article titles to Wikidata IDs for a language edition.

        Args:
            lang: Language edition code (e.g. "en").

        Returns:
            Dict mapping article_title -> wikidata_id for all persons
            that have an article title in the given language.
        """
        ...
