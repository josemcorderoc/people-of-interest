# Design: People of Interest

## Overview

A two-tier system — batch data pipeline and table-based web frontend — that ingests Wikipedia pageview data from an S3-cached dump archive, computes trending and popularity scores for notable people (~500K+ biographical entities), and presents them in a ranked, filterable table with profile images. All services run as Docker Compose containers. Shares the S3 pageview dump bucket with the Points of Interest project.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Docker Compose Services                        │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌───────────────────┐   │
│  │ person-sync   │   │ pageview-    │   │ score-compute     │   │
│  │ (weekly)     │   │ ingest       │   │ (daily, after     │   │
│  │              │   │ (daily)      │   │  pageview-ingest) │   │
│  └──────┬───────┘   └──────┬───────┘   └────────┬──────────┘   │
│         │                   │                     │              │
│         │          ┌────────┴──────┐              │              │
│         │          │ S3 Bucket     │              │              │
│         │          │ (shared with  │              │              │
│         │          │ POI project)  │              │              │
│         │          └────────┬──────┘              │              │
│         ▼                   ▼                     ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   db (PostgreSQL)                        │    │
│  │  persons │ pageviews_daily │ scores_daily │ pipeline_log │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────────────────────┴──────────────────────────────┐   │
│  │                   api (Python / FastAPI)                   │   │
│  │  GET /persons?view=...&window=...&category=...&page=...   │   │
│  │  GET /persons/:id/detail?window=...                       │   │
│  │  GET /persons/search?q=...                                │   │
│  └───────────────────────────┬──────────────────────────────┘   │
│                              │                                   │
│  ┌───────────────────────────┴──────────────────────────────┐   │
│  │                   frontend (React)                         │   │
│  │  Ranked table with images, filters, search, detail panel  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Model

### persons

| Column | Type | Notes |
|--------|------|-------|
| wikidata_id | TEXT (PK) | e.g. "Q76" (Barack Obama) |
| name | TEXT | English label |
| names_by_lang | JSONB | `{"en": "Barack Obama", "ja": "バラク・オバマ"}` |
| article_titles | JSONB | `{"en": "Barack Obama", "ja": "バラク・オバマ"}` |
| category | TEXT | Mapped from P106: politician, athlete, artist, scientist, business, writer, historical, other |
| birth_date | DATE | P569, nullable |
| death_date | DATE | P577, nullable for living people |
| nationality | TEXT | P27, primary nationality |
| occupations | JSONB | Full list from P106 as array |
| image_filename | TEXT | P18 value (Wikimedia Commons filename), nullable |
| gender | TEXT | P21: male, female, other, unknown |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

Indexes: B-tree on `category`, GIN on `name` + `names_by_lang` values for search.

### pageviews_daily

| Column | Type | Notes |
|--------|------|-------|
| person_id | TEXT (FK → persons.wikidata_id) | |
| lang | TEXT | Language edition code |
| date | DATE | |
| views | INTEGER | Raw pageview count |

PK: `(person_id, lang, date)`. Partitioned by month on `date`.

### scores_daily

| Column | Type | Notes |
|--------|------|-------|
| person_id | TEXT (FK → persons.wikidata_id) | |
| date | DATE | |
| window | TEXT | 'daily', 'weekly', 'monthly' |
| popularity | BIGINT | Total views across all languages |
| trending_zscore | FLOAT | Z-score over 30-day rolling mean |

PK: `(person_id, date, window)`. Partitioned by month on `date`.

## Data Pipeline

### Shared S3 Data Source

Pageview dump files are stored at `s3://poi-pageview-dumps/pageviews/{year}/{year-month}/pageviews-{YYYYMMDD}-user.bz2`. These are downloaded and cached by the Points of Interest project. The People of Interest project reads from the same bucket — **never downloads from Wikimedia directly**.

### Person Sync (weekly)

Stream-processes the Wikidata JSON dump to extract items with P31=Q5 (human) that have:
- At least one sitelink in configured language editions
- P569 (date of birth) — required to confirm biographical entity

Maps P106 (occupation) QIDs to categories:

| P106 QIDs | Category |
|-----------|----------|
| Q82955 (politician), Q193391 (diplomat), Q116 (monarch), ... | politician |
| Q2066131 (athlete), Q937857 (footballer), ... | athlete |
| Q33999 (actor), Q177220 (singer), Q639669 (musician), ... | artist |
| Q901 (scientist), Q1622272 (professor), ... | scientist |
| Q43845 (businessperson), Q484876 (CEO), ... | business |
| Q36180 (writer), Q4853732 (author), ... | writer |
| Others with death_date < 1900 | historical |
| Unmapped | other |

### Pageview Ingest (daily)

1. Read dump file from S3 for yesterday
2. Parse all languages, filter to persons in registry
3. Bulk insert into pageviews_daily

### Score Compute (daily)

Batch SQL computation:
- Popularity: `SUM(views)` per person per window
- Trending z-score: `(today - mean_30d) / stddev_30d`

## Serving Layer

**FastAPI** application.

### Endpoints

**`GET /persons`** — Ranked table data.
- Params: `view` (trending|popularity), `window` (daily|weekly|monthly), `category` (comma-separated filter), `langs` (comma-separated, default: en), `date` (default: latest), `page` (default: 1), `per_page` (default: 50), `sort` (rank|name|category|score), `order` (asc|desc).
- Returns: `{ total, page, per_page, results: [{ wikidata_id, rank, name, category, score, image_url, sparkline_7d }] }`

**`GET /persons/{id}/detail`** — Full detail.
- Params: `window` (daily|weekly|monthly).
- Returns: person metadata, all scores, sparkline (30d/12w/12m), language breakdown, Wikipedia links for all editions.

**`GET /persons/search`** — Name search.
- Params: `q`, `limit` (default 20).
- Returns: matching persons with id, name, category, image_url.

**`GET /config`** — Available categories, languages, date range.

### Image URLs

Profile images are served via Wikimedia Commons `Special:FilePath`:
```
https://commons.wikimedia.org/wiki/Special:FilePath/{filename}?width=80
```
The `image_filename` from Wikidata P18 is URL-encoded and appended. Width parameter controls thumbnail size.

## Frontend Architecture

### Technology

- **React 19** + TypeScript + Vite
- **TanStack Query** — data fetching with pagination
- **TanStack Table** — headless table with sorting, filtering
- **Tailwind CSS** — styling

### Component Tree

```
<App>
  <Header>
    <DatePicker />
    <ViewToggle />           # Trending / Popularity
    <WindowSelector />       # Daily / Weekly / Monthly
    <CategoryFilter />       # Multi-select occupation filter
    <LanguageSelector />     # Multi-select language editions
    <SearchBox />            # Filter by name
  </Header>
  <PersonTable>
    <TableRow>               # Rank, Image, Name (link), Category badge, Score, Mini sparkline
    </TableRow>
    <Pagination />
  </PersonTable>
  <PersonDetail />           # Expandable row or side panel
</App>
```

### State Management

URL-based state via query parameters:
- `?view=trending&window=daily&category=politician,athlete&langs=en,fr&date=2026-04-04&page=1&q=`

This makes the table shareable via URL.
