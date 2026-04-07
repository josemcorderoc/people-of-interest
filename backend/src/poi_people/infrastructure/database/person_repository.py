"""SQLAlchemy implementation of the PersonRepository protocol."""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from poi_people.domain.entities.person import Person
from poi_people.infrastructure.database import models


class SqlPersonRepository:
    """SQLAlchemy-backed PersonRepository implementation."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def upsert_batch(self, persons: list[Person]) -> int:
        """Insert or update a batch of persons using PostgreSQL ON CONFLICT."""
        if not persons:
            return 0

        async with self._session_factory() as session:
            values = [
                {
                    "wikidata_id": p.wikidata_id,
                    "name": p.name,
                    "names_by_lang": p.names_by_lang,
                    "article_titles": p.article_titles,
                    "category": p.category,
                    "birth_date": p.birth_date,
                    "death_date": p.death_date,
                    "nationality": p.nationality,
                    "occupations": p.occupations,
                    "image_filename": p.image_filename,
                    "gender": p.gender,
                }
                for p in persons
            ]

            stmt = pg_insert(models.Person).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["wikidata_id"],
                set_={
                    "name": stmt.excluded.name,
                    "names_by_lang": stmt.excluded.names_by_lang,
                    "article_titles": stmt.excluded.article_titles,
                    "category": stmt.excluded.category,
                    "birth_date": stmt.excluded.birth_date,
                    "death_date": stmt.excluded.death_date,
                    "nationality": stmt.excluded.nationality,
                    "occupations": stmt.excluded.occupations,
                    "image_filename": stmt.excluded.image_filename,
                    "gender": stmt.excluded.gender,
                },
            )
            await session.execute(stmt)
            await session.commit()
            return len(persons)

    async def get_by_id(self, wikidata_id: str) -> Person | None:
        """Retrieve a person by Wikidata ID."""
        async with self._session_factory() as session:
            stmt = select(models.Person).where(models.Person.wikidata_id == wikidata_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return _row_to_domain(row)

    async def search_by_text(self, query: str, limit: int = 20) -> list[Person]:
        """Search persons by name using trigram similarity."""
        async with self._session_factory() as session:
            stmt = (
                select(models.Person)
                .where(models.Person.search_text.ilike(f"%{query}%"))
                .order_by(models.Person.name)
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [_row_to_domain(r) for r in rows]

    async def get_article_title_mapping(self, lang: str) -> dict[str, str]:
        """Get mapping of article titles to Wikidata IDs for a language."""
        async with self._session_factory() as session:
            stmt = text(
                "SELECT wikidata_id, article_titles->>:lang AS title "
                "FROM persons "
                "WHERE article_titles ? :lang"
            )
            result = await session.execute(stmt, {"lang": lang})
            return {row.title: row.wikidata_id for row in result if row.title}


def _row_to_domain(row: models.Person) -> Person:
    """Convert a SQLAlchemy Person model to a domain Person entity."""
    return Person(
        wikidata_id=row.wikidata_id,
        name=row.name,
        names_by_lang=row.names_by_lang or {},
        article_titles=row.article_titles or {},
        category=row.category,
        birth_date=row.birth_date,
        death_date=row.death_date,
        nationality=row.nationality,
        occupations=row.occupations or [],
        image_filename=row.image_filename,
        gender=row.gender or "unknown",
    )
