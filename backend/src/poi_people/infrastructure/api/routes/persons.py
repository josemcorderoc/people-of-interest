"""GET /api/persons — ranked person listing with pagination and filtering."""

from __future__ import annotations

import datetime
from urllib.parse import quote

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from poi_people.infrastructure.database.models import PageviewDaily, Person, ScoreDaily

router = APIRouter(prefix="/api", tags=["persons"])


class PersonResult(BaseModel):
    wikidata_id: str
    rank: int
    name: str
    category: str
    score: float | None
    image_url: str | None
    sparkline_7d: list[int]


class PersonsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    results: list[PersonResult]


def _image_url(filename: str | None) -> str | None:
    if not filename:
        return None
    encoded = quote(filename, safe="")
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{encoded}?width=80"


@router.get("/persons", response_model=PersonsResponse)
async def get_persons(
    request: Request,
    view: str = Query("popularity", pattern="^(trending|popularity)$"),
    window: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    category: list[str] | None = Query(None),
    langs: list[str] | None = Query(None),
    date: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort: str = Query("score", pattern="^(score|name)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> PersonsResponse:
    """Return ranked persons with scores, images, and sparkline data."""
    session_factory = request.app.state.session_factory

    async with session_factory() as session:
        # Determine the score date
        score_date = _parse_date_or_latest(date, session, window)
        if isinstance(score_date, datetime.date):
            resolved_date = score_date
        else:
            resolved_date = await score_date

        score_column = "trending_zscore" if view == "trending" else "popularity"

        # If langs provided, compute per-language popularity instead of using pre-computed scores
        if langs:
            return await _query_with_lang_filter(
                session, resolved_date, window, langs, category,
                page, per_page, sort, order, view,
            )

        return await _query_precomputed(
            session, resolved_date, window, score_column, category,
            page, per_page, sort, order,
        )


async def _parse_date_or_latest(
    date_str: str | None, session: AsyncSession, window: str
) -> datetime.date:
    """Parse a date string or find the latest available score date."""
    if date_str:
        return datetime.date.fromisoformat(date_str)

    result = await session.execute(
        select(func.max(ScoreDaily.date)).where(ScoreDaily.window == window)
    )
    latest = result.scalar()
    if latest:
        return latest
    return datetime.date.today()


async def _query_precomputed(
    session: AsyncSession,
    score_date: datetime.date,
    window: str,
    score_column: str,
    categories: list[str] | None,
    page: int,
    per_page: int,
    sort: str,
    order: str,
) -> PersonsResponse:
    """Query using pre-computed scores."""
    sort_col = getattr(ScoreDaily, score_column) if sort == "score" else Person.name

    base = (
        select(
            Person.wikidata_id,
            Person.name,
            Person.category,
            Person.image_filename,
            getattr(ScoreDaily, score_column).label("score"),
        )
        .join(ScoreDaily, ScoreDaily.person_id == Person.wikidata_id)
        .where(ScoreDaily.date == score_date, ScoreDaily.window == window)
    )

    if categories:
        base = base.where(Person.category.in_(categories))

    # Count total
    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    # Apply ordering
    if sort == "score":
        if order == "desc":
            base = base.order_by(sort_col.desc().nulls_last())
        else:
            base = base.order_by(sort_col.asc().nulls_last())
    else:
        if order == "desc":
            base = base.order_by(Person.name.desc())
        else:
            base = base.order_by(Person.name.asc())

    offset = (page - 1) * per_page
    rows = (await session.execute(base.limit(per_page).offset(offset))).all()

    # Get person IDs for sparkline
    person_ids = [r.wikidata_id for r in rows]
    sparklines = await _get_sparklines(session, person_ids, score_date)

    results = []
    for idx, row in enumerate(rows):
        results.append(PersonResult(
            wikidata_id=row.wikidata_id,
            rank=offset + idx + 1,
            name=row.name,
            category=row.category,
            score=float(row.score) if row.score is not None else None,
            image_url=_image_url(row.image_filename),
            sparkline_7d=sparklines.get(row.wikidata_id, []),
        ))

    return PersonsResponse(total=total, page=page, per_page=per_page, results=results)


async def _query_with_lang_filter(
    session: AsyncSession,
    score_date: datetime.date,
    window: str,
    langs: list[str],
    categories: list[str] | None,
    page: int,
    per_page: int,
    sort: str,
    order: str,
    view: str,
) -> PersonsResponse:
    """Query with per-language popularity computed from pageviews_daily."""
    window_days = {"daily": 1, "weekly": 7, "monthly": 30}
    days = window_days.get(window, 1)
    start_date = score_date - datetime.timedelta(days=days - 1)

    # Build per-language popularity subquery
    pv_sub = (
        select(
            PageviewDaily.person_id,
            func.sum(PageviewDaily.views).label("popularity"),
        )
        .where(
            PageviewDaily.date >= start_date,
            PageviewDaily.date <= score_date,
            PageviewDaily.lang.in_(langs),
        )
        .group_by(PageviewDaily.person_id)
        .subquery()
    )

    # For trending, join with pre-computed z-scores
    if view == "trending":
        base = (
            select(
                Person.wikidata_id,
                Person.name,
                Person.category,
                Person.image_filename,
                ScoreDaily.trending_zscore.label("score"),
            )
            .join(ScoreDaily, ScoreDaily.person_id == Person.wikidata_id)
            .join(pv_sub, pv_sub.c.person_id == Person.wikidata_id)
            .where(ScoreDaily.date == score_date, ScoreDaily.window == window)
        )
    else:
        base = (
            select(
                Person.wikidata_id,
                Person.name,
                Person.category,
                Person.image_filename,
                pv_sub.c.popularity.label("score"),
            )
            .join(pv_sub, pv_sub.c.person_id == Person.wikidata_id)
        )

    if categories:
        base = base.where(Person.category.in_(categories))

    count_q = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    if sort == "score":
        if order == "desc":
            base = base.order_by(text("score DESC NULLS LAST"))
        else:
            base = base.order_by(text("score ASC NULLS LAST"))
    else:
        if order == "desc":
            base = base.order_by(Person.name.desc())
        else:
            base = base.order_by(Person.name.asc())

    offset = (page - 1) * per_page
    rows = (await session.execute(base.limit(per_page).offset(offset))).all()

    person_ids = [r.wikidata_id for r in rows]
    sparklines = await _get_sparklines(session, person_ids, score_date, langs)

    results = []
    for idx, row in enumerate(rows):
        results.append(PersonResult(
            wikidata_id=row.wikidata_id,
            rank=offset + idx + 1,
            name=row.name,
            category=row.category,
            score=float(row.score) if row.score is not None else None,
            image_url=_image_url(row.image_filename),
            sparkline_7d=sparklines.get(row.wikidata_id, []),
        ))

    return PersonsResponse(total=total, page=page, per_page=per_page, results=results)


async def _get_sparklines(
    session: AsyncSession,
    person_ids: list[str],
    end_date: datetime.date,
    langs: list[str] | None = None,
) -> dict[str, list[int]]:
    """Get last 7 days of daily popularity for a batch of persons."""
    if not person_ids:
        return {}

    start_date = end_date - datetime.timedelta(days=6)

    base = (
        select(
            PageviewDaily.person_id,
            PageviewDaily.date,
            func.sum(PageviewDaily.views).label("total"),
        )
        .where(
            PageviewDaily.person_id.in_(person_ids),
            PageviewDaily.date >= start_date,
            PageviewDaily.date <= end_date,
        )
    )

    if langs:
        base = base.where(PageviewDaily.lang.in_(langs))

    base = base.group_by(PageviewDaily.person_id, PageviewDaily.date).order_by(
        PageviewDaily.person_id, PageviewDaily.date
    )

    rows = (await session.execute(base)).all()

    # Build sparkline dict with zero-filled 7-day arrays
    result: dict[str, dict[datetime.date, int]] = {}
    for row in rows:
        result.setdefault(row.person_id, {})[row.date] = int(row.total)

    sparklines: dict[str, list[int]] = {}
    for pid in person_ids:
        daily = result.get(pid, {})
        sparklines[pid] = [
            daily.get(start_date + datetime.timedelta(days=i), 0) for i in range(7)
        ]

    return sparklines
