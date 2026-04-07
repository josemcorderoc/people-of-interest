"""Seed script — populate the database with ~30 notable persons and synthetic data for testing."""

from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import math
import random

from poi_people.domain.entities.pageview_record import PageviewRecord
from poi_people.domain.entities.person import Person
from poi_people.domain.entities.score_record import ScoreRecord
from poi_people.infrastructure.database.engine import create_engine, create_session_factory
from poi_people.infrastructure.database.pageview_repository import SqlPageviewRepository
from poi_people.infrastructure.database.person_repository import SqlPersonRepository
from poi_people.infrastructure.database.score_repository import SqlScoreRepository

logger = logging.getLogger(__name__)

def _person(  # noqa: PLR0913
    qid: str, name: str, cat: str, born: str, img: str,
    gender: str = "male", nat: str = "Q30", occs: list[str] | None = None,
    died: str | None = None, titles: dict[str, str] | None = None,
) -> dict:
    d: dict = {
        "wikidata_id": qid, "name": name, "category": cat,
        "birth_date": born, "nationality": nat,
        "occupations": occs or [], "image_filename": img,
        "gender": gender, "article_titles": titles or {"en": name},
    }
    if died:
        d["death_date"] = died
    return d


SEED_PERSONS: list[dict] = [
    _person("Q76", "Barack Obama", "politician", "1961-08-04",
            "President Barack Obama.jpg", occs=["Q82955"],
            titles={"en": "Barack Obama", "es": "Barack Obama",
                    "fr": "Barack Obama", "de": "Barack Obama"}),
    _person("Q615", "Lionel Messi", "athlete", "1987-06-24",
            "Lionel Messi 20180626.jpg", nat="Q414", occs=["Q937857"],
            titles={"en": "Lionel Messi", "es": "Lionel Messi",
                    "fr": "Lionel Messi"}),
    _person("Q26876", "Taylor Swift", "artist", "1989-12-13",
            "Taylor Swift at the 2023 MTV VMAs 4.png", gender="female",
            occs=["Q177220"],
            titles={"en": "Taylor Swift", "es": "Taylor Swift",
                    "fr": "Taylor Swift"}),
    _person("Q937", "Albert Einstein", "scientist", "1879-03-14",
            "Einstein 1921 by F Schmutzer.jpg", nat="Q183",
            occs=["Q169470"], died="1955-04-18",
            titles={"en": "Albert Einstein", "es": "Albert Einstein",
                    "de": "Albert Einstein"}),
    _person("Q5284", "Bill Gates", "business", "1955-10-28",
            "Bill Gates 2017 (cropped).jpg", occs=["Q43845"],
            titles={"en": "Bill Gates", "es": "Bill Gates"}),
    _person("Q36844", "J. K. Rowling", "writer", "1965-07-31",
            "J. K. Rowling 2010.jpg", gender="female", nat="Q145",
            occs=["Q36180"],
            titles={"en": "J. K. Rowling", "es": "J. K. Rowling",
                    "fr": "J. K. Rowling"}),
    _person("Q1299", "The Beatles", "artist", "1960-08-01",
            "The Beatles in 1964.jpg", gender="other", nat="Q145",
            occs=["Q639669"],
            titles={"en": "The Beatles", "es": "The Beatles"}),
    _person("Q567", "Angela Merkel", "politician", "1954-07-17",
            "Angela Merkel 2019 cropped.jpg", gender="female", nat="Q183",
            occs=["Q82955"],
            titles={"en": "Angela Merkel", "de": "Angela Merkel",
                    "fr": "Angela Merkel"}),
    _person("Q5582", "Marie Curie", "scientist", "1867-11-07",
            "Marie Curie c. 1920s.jpg", gender="female", nat="Q36",
            occs=["Q593644"], died="1934-07-04",
            titles={"en": "Marie Curie", "fr": "Marie Curie",
                    "pl": "Maria Sklodowska-Curie"}),
    _person("Q7747", "Cristiano Ronaldo", "athlete", "1985-02-05",
            "Cristiano Ronaldo 2018.jpg", nat="Q45", occs=["Q937857"],
            titles={"en": "Cristiano Ronaldo",
                    "es": "Cristiano Ronaldo",
                    "pt": "Cristiano Ronaldo"}),
    _person("Q36215", "Elon Musk", "business", "1971-06-28",
            "Elon Musk Royal Society.jpg", nat="Q258",
            occs=["Q131524"],
            titles={"en": "Elon Musk", "es": "Elon Musk",
                    "de": "Elon Musk"}),
    _person("Q1339", "Johann Sebastian Bach", "artist", "1685-03-31",
            "Johann Sebastian Bach.jpg", nat="Q183", occs=["Q639669"],
            died="1750-07-28",
            titles={"en": "Johann Sebastian Bach",
                    "de": "Johann Sebastian Bach"}),
    _person("Q859", "Abraham Lincoln", "politician", "1809-02-12",
            "Abraham Lincoln O-77.jpg", occs=["Q82955", "Q30461"],
            died="1865-04-15",
            titles={"en": "Abraham Lincoln",
                    "es": "Abraham Lincoln"}),
    _person("Q1124", "Stephen Hawking", "scientist", "1942-01-08",
            "Stephen Hawking.StarChild.jpg", nat="Q145",
            occs=["Q169470"], died="2018-03-14",
            titles={"en": "Stephen Hawking",
                    "de": "Stephen Hawking"}),
    _person("Q254", "Wolfgang Amadeus Mozart", "artist", "1756-01-27",
            "Wolfgang Amadeus Mozart Signature.svg", nat="Q40",
            occs=["Q639669"], died="1791-12-05",
            titles={"en": "Wolfgang Amadeus Mozart",
                    "de": "Wolfgang Amadeus Mozart"}),
    _person("Q1930", "Napoleon", "politician", "1769-08-15",
            "Napoleon in His Study.jpg", nat="Q142",
            occs=["Q82955"], died="1821-05-05",
            titles={"en": "Napoleon", "fr": "Napoleon Ier",
                    "es": "Napoleon Bonaparte"}),
    _person("Q36153", "Oprah Winfrey", "artist", "1954-01-29",
            "Oprah Winfrey 2010.jpg", gender="female",
            occs=["Q33999"],
            titles={"en": "Oprah Winfrey",
                    "es": "Oprah Winfrey"}),
    _person("Q11862", "Mahatma Gandhi", "politician", "1869-10-02",
            "Mahatma-Gandhi, studio, 1931.jpg", nat="Q668",
            occs=["Q82955"], died="1948-01-30",
            titles={"en": "Mahatma Gandhi"}),
    _person("Q2831", "Michael Jordan", "athlete", "1963-02-17",
            "Michael Jordan in 2014.jpg", occs=["Q10843263"],
            titles={"en": "Michael Jordan",
                    "es": "Michael Jordan"}),
    _person("Q484523", "LeBron James", "athlete", "1984-12-30",
            "LeBron James (cropped).jpg", occs=["Q10843263"],
            titles={"en": "LeBron James",
                    "es": "LeBron James"}),
    _person("Q4263842", "Serena Williams", "athlete", "1981-09-26",
            "Serena Williams at 2013 US Open.jpg", gender="female",
            occs=["Q2066131"],
            titles={"en": "Serena Williams"}),
    _person("Q36949", "Adele", "artist", "1988-05-05",
            "Adele Glasgow 2016.jpg", gender="female", nat="Q145",
            occs=["Q177220"],
            titles={"en": "Adele", "es": "Adele", "fr": "Adele"}),
    _person("Q317521", "Beyonce", "artist", "1981-09-04",
            "Beyonce Formation Tour.jpg", gender="female",
            occs=["Q177220"],
            titles={"en": "Beyonce", "es": "Beyonce",
                    "fr": "Beyonce"}),
    _person("Q5879", "Leonardo da Vinci", "artist", "1452-04-15",
            "Portrait of Leonardo.png", nat="Q38",
            occs=["Q33999"], died="1519-05-02",
            titles={"en": "Leonardo da Vinci",
                    "it": "Leonardo da Vinci",
                    "es": "Leonardo da Vinci"}),
    _person("Q8023", "Nelson Mandela", "politician", "1918-07-18",
            "Nelson Mandela-2008 (edit).jpg", nat="Q258",
            occs=["Q82955", "Q30461"], died="2013-12-05",
            titles={"en": "Nelson Mandela"}),
    _person("Q255", "Ludwig van Beethoven", "artist", "1770-12-17",
            "Beethoven.jpg", nat="Q183", occs=["Q639669"],
            died="1827-03-26",
            titles={"en": "Ludwig van Beethoven",
                    "de": "Ludwig van Beethoven"}),
    _person("Q7186", "Marie Antoinette", "historical", "1755-11-02",
            "Marie-Antoinette 1775.jpg", gender="female", nat="Q142",
            occs=["Q116"], died="1793-10-16",
            titles={"en": "Marie Antoinette",
                    "fr": "Marie-Antoinette"}),
    _person("Q5593", "Nikola Tesla", "scientist", "1856-07-10",
            "N.Tesla.JPG", occs=["Q169470"], died="1943-01-07",
            titles={"en": "Nikola Tesla", "de": "Nikola Tesla"}),
    _person("Q34086", "Haruki Murakami", "writer", "1949-01-12",
            "Haruki Murakami (2009).jpg", nat="Q17",
            occs=["Q6625963"],
            titles={"en": "Haruki Murakami", "ja": "村上春樹"}),
    _person("Q160", "Cleopatra", "historical", "0069-01-01",
            "Kleopatra-VII.jpg", gender="female", nat="Q79",
            occs=["Q116"], died="0030-08-12",
            titles={"en": "Cleopatra", "es": "Cleopatra"}),
]

LANGS = ["en", "es", "fr", "de", "ja", "pt", "it", "pl", "ru", "zh"]


def _make_person(d: dict) -> Person:
    """Create a Person domain entity from seed dict."""
    return Person(
        wikidata_id=d["wikidata_id"],
        name=d["name"],
        names_by_lang={lang: d["name"] for lang in d.get("article_titles", {})},
        article_titles=d.get("article_titles", {}),
        category=d["category"],
        birth_date=datetime.date.fromisoformat(d["birth_date"]) if d.get("birth_date") else None,
        death_date=datetime.date.fromisoformat(d["death_date"]) if d.get("death_date") else None,
        nationality=d.get("nationality"),
        occupations=d.get("occupations", []),
        image_filename=d.get("image_filename"),
        gender=d.get("gender", "unknown"),
    )


def _generate_pageviews(
    persons: list[Person], days: int, ref_date: datetime.date
) -> list[PageviewRecord]:
    """Generate synthetic daily pageview records."""
    records = []
    random.seed(42)

    for person in persons:
        # Base popularity varies by category
        base = {"politician": 5000, "athlete": 8000, "artist": 7000, "scientist": 3000,
                "business": 4000, "writer": 2000, "historical": 1500, "other": 1000}
        base_views = base.get(person.category, 1000) + random.randint(-500, 2000)

        for d in range(days):
            date = ref_date - datetime.timedelta(days=d)
            # Add some trending variation: recent days get a spike for some persons
            spike = 1.0
            if d < 3 and random.random() < 0.3:
                spike = random.uniform(2.0, 5.0)

            for lang in person.article_titles:
                # English gets most views
                lang_factor = 1.0 if lang == "en" else random.uniform(0.1, 0.4)
                views = int(base_views * lang_factor * spike * random.uniform(0.7, 1.3))
                views = max(1, views)
                records.append(PageviewRecord(
                    person_id=person.wikidata_id,
                    lang=lang,
                    date=date,
                    views=views,
                ))

    return records


def _generate_scores(
    persons: list[Person], pageviews: list[PageviewRecord], days: int, ref_date: datetime.date
) -> list[ScoreRecord]:
    """Generate synthetic score records from pageview data."""
    # Group pageviews by (person_id, date)
    daily_totals: dict[tuple[str, datetime.date], int] = {}
    for pv in pageviews:
        key = (pv.person_id, pv.date)
        daily_totals[key] = daily_totals.get(key, 0) + pv.views

    records = []
    windows = {"daily": 1, "weekly": 7, "monthly": 30}

    for person in persons:
        for d in range(days):
            date = ref_date - datetime.timedelta(days=d)
            for window_name, window_days in windows.items():
                # Popularity = sum of views in window
                popularity = 0
                for wd in range(window_days):
                    wd_date = date - datetime.timedelta(days=wd)
                    popularity += daily_totals.get((person.wikidata_id, wd_date), 0)

                # Compute z-score from 30-day history
                hist = []
                for hd in range(1, 31):
                    hd_date = date - datetime.timedelta(days=hd)
                    hist.append(daily_totals.get((person.wikidata_id, hd_date), 0))

                if hist:
                    mean_val = sum(hist) / len(hist)
                    var = sum((x - mean_val) ** 2 for x in hist) / len(hist)
                    std = math.sqrt(var)
                    today_val = daily_totals.get((person.wikidata_id, date), 0)
                    zscore = (today_val - mean_val) / std if std > 0 else None
                else:
                    zscore = None

                records.append(ScoreRecord(
                    person_id=person.wikidata_id,
                    date=date,
                    window=window_name,
                    popularity=popularity,
                    trending_zscore=round(zscore, 4) if zscore is not None else None,
                ))

    return records


async def _run_seed(days: int) -> None:
    engine = create_engine()
    session_factory = create_session_factory(engine)

    person_repo = SqlPersonRepository(session_factory)
    pageview_repo = SqlPageviewRepository(session_factory)
    score_repo = SqlScoreRepository(session_factory)

    ref_date = datetime.date.today()
    persons = [_make_person(d) for d in SEED_PERSONS]

    logger.info("Seeding %d persons...", len(persons))
    await person_repo.upsert_batch(persons)

    logger.info("Generating pageviews for %d days...", days)
    pageviews = _generate_pageviews(persons, days, ref_date)
    logger.info("Inserting %d pageview records...", len(pageviews))

    # Batch insert pageviews
    batch_size = 500
    for i in range(0, len(pageviews), batch_size):
        await pageview_repo.insert_batch(pageviews[i : i + batch_size])

    logger.info("Generating scores...")
    scores = _generate_scores(persons, pageviews, days, ref_date)
    logger.info("Inserting %d score records...", len(scores))

    for i in range(0, len(scores), batch_size):
        await score_repo.insert_batch(scores[i : i + batch_size])

    await engine.dispose()
    logger.info("Seed complete!")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    parser = argparse.ArgumentParser(description="Seed database with test data")
    parser.add_argument("--days", type=int, default=45, help="Number of days of data to generate (default: 45)")
    args = parser.parse_args()

    asyncio.run(_run_seed(args.days))


if __name__ == "__main__":
    main()
