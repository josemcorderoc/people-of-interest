"""GET /api/persons/{id}/detail — detailed person info with sparklines and language breakdown."""

from __future__ import annotations

import datetime
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from poi_people.infrastructure.database.models import PageviewDaily, Person, ScoreDaily

router = APIRouter(prefix="/api", tags=["persons"])


class WikiLink(BaseModel):
    lang: str
    url: str
    title: str


class LanguageBreakdown(BaseModel):
    lang: str
    views: int


class PersonDetailResponse(BaseModel):
    wikidata_id: str
    name: str
    names_by_lang: dict[str, str]
    category: str
    birth_date: str | None
    death_date: str | None
    nationality: str | None
    occupations: list[str]
    gender: str
    image_url: str | None
    scores: dict[str, float | None]
    sparkline_30d: list[int]
    sparkline_12w: list[int]
    sparkline_12m: list[int]
    language_breakdown: list[LanguageBreakdown]
    wikipedia_links: list[WikiLink]


def _image_url(filename: str | None) -> str | None:
    if not filename:
        return None
    encoded = quote(filename, safe="")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=80"


@router.get("/persons/{person_id}/detail", response_model=PersonDetailResponse)
async def get_person_detail(
    person_id: str,
    request: Request,
    window: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
) -> PersonDetailResponse:
    """Return detailed information about a person."""
    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        # Fetch person
        result = await session.execute(
            select(Person).where(Person.wikidata_id == person_id)
        )
        person = result.scalar_one_or_none()
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")

        today = datetime.date.today()

        # Latest scores
        scores = await _get_latest_scores(session, person_id, window, today)

        # Sparklines
        sparkline_30d = await _get_daily_sparkline(session, person_id, today, 30)
        sparkline_12w = await _get_weekly_sparkline(session, person_id, today, 12)
        sparkline_12m = await _get_monthly_sparkline(session, person_id, today, 12)

        # Language breakdown (last 30 days)
        lang_breakdown = await _get_language_breakdown(session, person_id, today)

        # Wikipedia links
        article_titles = person.article_titles or {}
        wiki_links = [
            WikiLink(
                lang=lang,
                url=f"https://{lang}.wikipedia.org/wiki/{quote(title, safe='')}",
                title=title,
            )
            for lang, title in sorted(article_titles.items())
        ]

        return PersonDetailResponse(
            wikidata_id=person.wikidata_id,
            name=person.name,
            names_by_lang=person.names_by_lang or {},
            category=person.category,
            birth_date=str(person.birth_date) if person.birth_date else None,
            death_date=str(person.death_date) if person.death_date else None,
            nationality=person.nationality,
            occupations=person.occupations or [],
            gender=person.gender or "unknown",
            image_url=_image_url(person.image_filename),
            scores=scores,
            sparkline_30d=sparkline_30d,
            sparkline_12w=sparkline_12w,
            sparkline_12m=sparkline_12m,
            language_breakdown=lang_breakdown,
            wikipedia_links=wiki_links,
        )


async def _get_latest_scores(
    session: AsyncSession, person_id: str, window: str, ref_date: datetime.date
) -> dict[str, float | None]:
    """Get the latest popularity and trending scores."""
    result = await session.execute(
        select(ScoreDaily.popularity, ScoreDaily.trending_zscore)
        .where(
            ScoreDaily.person_id == person_id,
            ScoreDaily.window == window,
            ScoreDaily.date <= ref_date,
        )
        .order_by(ScoreDaily.date.desc())
        .limit(1)
    )
    row = result.first()
    if row is None:
        return {"popularity": None, "trending_zscore": None}
    return {
        "popularity": float(row.popularity) if row.popularity is not None else None,
        "trending_zscore": float(row.trending_zscore) if row.trending_zscore is not None else None,
    }


async def _get_daily_sparkline(
    session: AsyncSession, person_id: str, ref_date: datetime.date, days: int
) -> list[int]:
    """Daily total views for last N days."""
    start = ref_date - datetime.timedelta(days=days - 1)
    result = await session.execute(
        select(PageviewDaily.date, func.sum(PageviewDaily.views).label("total"))
        .where(
            PageviewDaily.person_id == person_id,
            PageviewDaily.date >= start,
            PageviewDaily.date <= ref_date,
        )
        .group_by(PageviewDaily.date)
        .order_by(PageviewDaily.date)
    )
    daily = {row.date: int(row.total) for row in result}
    return [daily.get(start + datetime.timedelta(days=i), 0) for i in range(days)]


async def _get_weekly_sparkline(
    session: AsyncSession, person_id: str, ref_date: datetime.date, weeks: int
) -> list[int]:
    """Weekly total views for last N weeks."""
    sparkline = []
    for w in range(weeks - 1, -1, -1):
        week_end = ref_date - datetime.timedelta(weeks=w)
        week_start = week_end - datetime.timedelta(days=6)
        result = await session.execute(
            select(func.coalesce(func.sum(PageviewDaily.views), 0))
            .where(
                PageviewDaily.person_id == person_id,
                PageviewDaily.date >= week_start,
                PageviewDaily.date <= week_end,
            )
        )
        sparkline.append(int(result.scalar()))
    return sparkline


async def _get_monthly_sparkline(
    session: AsyncSession, person_id: str, ref_date: datetime.date, months: int
) -> list[int]:
    """Monthly total views for last N months."""
    sparkline = []
    for m in range(months - 1, -1, -1):
        month_end = ref_date - datetime.timedelta(days=30 * m)
        month_start = month_end - datetime.timedelta(days=29)
        result = await session.execute(
            select(func.coalesce(func.sum(PageviewDaily.views), 0))
            .where(
                PageviewDaily.person_id == person_id,
                PageviewDaily.date >= month_start,
                PageviewDaily.date <= month_end,
            )
        )
        sparkline.append(int(result.scalar()))
    return sparkline


async def _get_language_breakdown(
    session: AsyncSession, person_id: str, ref_date: datetime.date
) -> list[LanguageBreakdown]:
    """Language breakdown of views over the last 30 days."""
    start = ref_date - datetime.timedelta(days=29)
    result = await session.execute(
        select(PageviewDaily.lang, func.sum(PageviewDaily.views).label("total"))
        .where(
            PageviewDaily.person_id == person_id,
            PageviewDaily.date >= start,
            PageviewDaily.date <= ref_date,
        )
        .group_by(PageviewDaily.lang)
        .order_by(func.sum(PageviewDaily.views).desc())
    )
    return [LanguageBreakdown(lang=row.lang, views=int(row.total)) for row in result]
