"""GET /api/persons/search — name search using pg_trgm."""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select

from poi_people.infrastructure.database.models import Person

router = APIRouter(prefix="/api", tags=["persons"])


class SearchResult(BaseModel):
    wikidata_id: str
    name: str
    category: str
    image_url: str | None


class SearchResponse(BaseModel):
    results: list[SearchResult]


def _image_url(filename: str | None) -> str | None:
    if not filename:
        return None
    encoded = quote(filename, safe="")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=80"


@router.get("/persons/search", response_model=SearchResponse)
async def search_persons(
    request: Request,
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    """Search persons by name using trigram similarity.

    Uses the pg_trgm GIN index on search_text for fast fuzzy matching.
    """
    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        # Use ILIKE for broad matching against search_text (which includes all language names)
        stmt = (
            select(
                Person.wikidata_id,
                Person.name,
                Person.category,
                Person.image_filename,
            )
            .where(Person.search_text.ilike(f"%{q}%"))
            .order_by(
                # Prefer exact-ish matches by similarity
                func.similarity(Person.search_text, q).desc(),
                Person.name,
            )
            .limit(limit)
        )

        rows = (await session.execute(stmt)).all()

        return SearchResponse(
            results=[
                SearchResult(
                    wikidata_id=row.wikidata_id,
                    name=row.name,
                    category=row.category,
                    image_url=_image_url(row.image_filename),
                )
                for row in rows
            ]
        )
