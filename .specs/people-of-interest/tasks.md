# Tasks: People of Interest

## Task List

### Phase 1: Project Bootstrapping

- [ ] **T-1: Initialize repository and Docker Compose**
  - Description: Create GitHub repo. Set up Python backend with uv, pyproject.toml, FastAPI, SQLAlchemy 2.x, Alembic, asyncpg. Docker Compose with `db` (PostgreSQL), `db-migrate`. Project structure following Clean Architecture. Add `.specs/`, `.claude/` directories with SDD agents.
  - Dependencies: none
  - Traces: NFR-006
  - Acceptance: `docker compose up db` starts PostgreSQL. Project structure follows Clean Architecture.

- [ ] **T-2: Configuration module**
  - Description: YAML config with language editions, scoring parameters, P106 occupation-to-category mapping, pipeline settings, S3 bucket configuration.
  - Dependencies: T-1
  - Traces: FR-003, NFR-007
  - Acceptance: Config loads and validates. P106 mapping covers major occupation QIDs.

- [ ] **T-3: Database schema and migrations**
  - Description: Alembic migration for `persons`, `pageviews_daily` (partitioned by month), `scores_daily` (partitioned by month), `pipeline_log`. Search index on names.
  - Dependencies: T-1
  - Traces: FR-001, FR-008
  - Acceptance: Tables created, partitions for current + 4 future months, search index working.

### Phase 2: Domain Layer

- [ ] **T-4: Domain entities and repository interfaces**
  - Description: Dataclasses/Pydantic models for Person, PageviewRecord, ScoreRecord, PipelineRun. Repository protocols. Source adapter protocol.
  - Dependencies: T-1
  - Traces: —
  - Acceptance: All models importable and tested. Protocols defined.

### Phase 3: Infrastructure — Adapters and Repositories

- [ ] **T-5: Wikidata person adapter**
  - Description: Stream-process Wikidata dump to extract P31=Q5 items with P569, sitelinks. Extract P106 occupations, P18 image, P21 gender, P27 nationality. Map occupations to categories.
  - Dependencies: T-4, T-2
  - Traces: FR-001, FR-002, FR-003
  - Acceptance: Adapter parses fixture dump, yields Person objects with all fields. Category mapping tested.

- [ ] **T-6: S3 pageview reader**
  - Description: Read pageview dump files from S3 bucket. Parse bz2 format. Filter to persons in registry. Uses boto3 with configurable bucket name.
  - Dependencies: T-4
  - Traces: FR-005, FR-006, FR-007, NFR-007
  - Acceptance: Reads dump from S3, parses, filters to known persons. Falls back gracefully if S3 unavailable.

- [ ] **T-7: Database repositories**
  - Description: SQLAlchemy implementations of PersonRepository, PageviewRepository, ScoreRepository, PipelineLogRepository.
  - Dependencies: T-3, T-4
  - Traces: FR-008
  - Acceptance: All CRUD operations tested against Docker DB.

### Phase 4: Pipeline

- [ ] **T-8: Person sync use case**
  - Description: Orchestrate Wikidata adapter with person repository. Pipeline logging, retry, structured JSON logging.
  - Dependencies: T-5, T-7
  - Traces: FR-001, FR-004
  - Acceptance: Syncs persons from dump to DB. Pipeline log updated.

- [ ] **T-9: Pageview ingest use case**
  - Description: Read dumps from S3, filter to person registry, bulk insert. Data quality checks.
  - Dependencies: T-6, T-7
  - Traces: FR-006, FR-007, FR-008
  - Acceptance: Ingests pageviews from S3 dump into DB.

- [ ] **T-10: Score computation**
  - Description: Batch SQL computation of popularity and z-score for all persons per window. Efficient — SQL-based, not Python-per-entity.
  - Dependencies: T-7, T-9
  - Traces: FR-009, FR-010, FR-011
  - Acceptance: Scores computed for all windows. Batch SQL approach completes in <10 min for 500K persons.

- [ ] **T-11: Backfill orchestration**
  - Description: Script to backfill from S3 dumps: person sync, then ingest pageviews for date range, then compute scores. Resumable.
  - Dependencies: T-8, T-9, T-10
  - Traces: FR-005
  - Acceptance: Backfills from S3 for a date range.

### Phase 5: API

- [ ] **T-12: FastAPI scaffold and /config**
  - Description: App factory, CORS, structured logging, `/config` endpoint.
  - Dependencies: T-2, T-7
  - Traces: NFR-006
  - Acceptance: API starts, /config returns categories and languages.

- [ ] **T-13: GET /persons ranked table endpoint**
  - Description: Paginated, sorted, filtered. Supports view/window/category/langs/date/page/sort. Returns image URLs constructed from P18 filename.
  - Dependencies: T-12, T-7
  - Traces: FR-013, FR-014, FR-015, FR-016
  - Acceptance: Returns 50 persons per page with ranks, scores, image URLs, 7-day sparkline.

- [ ] **T-14: GET /persons/{id}/detail**
  - Description: Full person detail with sparkline, language breakdown, Wikipedia links for all editions.
  - Dependencies: T-12, T-7
  - Traces: FR-024, FR-025
  - Acceptance: Returns complete detail. Wikipedia links for all editions with articles.

- [ ] **T-15: GET /persons/search**
  - Description: Name search across languages.
  - Dependencies: T-12, T-7
  - Traces: FR-022
  - Acceptance: Partial name matches work. Returns persons with image URLs.

### Phase 6: Frontend

- [ ] **T-16: React app scaffold**
  - Description: Vite + React 19 + TypeScript + Tailwind + TanStack Query + TanStack Table. Docker Compose frontend service.
  - Dependencies: T-1
  - Traces: NFR-006
  - Acceptance: `docker compose up frontend` serves the app.

- [ ] **T-17: Person table with images**
  - Description: Ranked table using TanStack Table. Columns: rank, image thumbnail (lazy loaded from Commons), name (hyperlink to Wikipedia), category badge, score, 7-day sparkline. Pagination.
  - Dependencies: T-16, T-13
  - Traces: FR-013, FR-014, FR-015, FR-016, NFR-001, NFR-002, NFR-003
  - Acceptance: 50 rows render in <2s. Images lazy load. Pagination works.

- [ ] **T-18: Control bar**
  - Description: ViewToggle, WindowSelector, CategoryFilter, LanguageSelector, DatePicker, SearchBox. All drive URL-based state.
  - Dependencies: T-16, T-12
  - Traces: FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023
  - Acceptance: All controls functional. URL reflects state. Shareable links work.

- [ ] **T-19: Person detail panel**
  - Description: Expandable row or side panel with full detail, larger photo, sparkline chart, language breakdown, Wikipedia links.
  - Dependencies: T-16, T-14
  - Traces: FR-024, FR-025
  - Acceptance: Detail shows all fields. Wikipedia links open in new tab.

### Phase 7: Integration

- [ ] **T-20: Seed data and E2E tests**
  - Description: Seed script with ~50 notable persons. Playwright E2E tests.
  - Dependencies: T-17, T-18, T-19
  - Traces: —
  - Acceptance: E2E tests pass. Seed data includes diverse categories.

- [ ] **T-21: Documentation**
  - Description: README, DATA_SOURCES.md, setup instructions.
  - Dependencies: T-20
  - Traces: —
  - Acceptance: New developer can clone and run.

## Dependency Graph

```
T-1 (repo + docker)
├── T-2 (config)
│   ├── T-5 (wikidata person adapter) ◄── T-4
│   └── T-12 (api scaffold) ◄── T-7
├── T-3 (db schema)
│   └── T-7 (repositories) ◄── T-4
├── T-4 (domain entities)
│   ├── T-5, T-6, T-7
└── T-16 (frontend scaffold)
    ├── T-17 (person table) ◄── T-13
    ├── T-18 (control bar) ◄── T-12
    └── T-19 (detail panel) ◄── T-14

T-5 + T-7 → T-8 (person sync)
T-6 + T-7 → T-9 (pageview ingest)
T-7 + T-9 → T-10 (score compute)
T-8 + T-9 + T-10 → T-11 (backfill)
T-12 + T-7 → T-13, T-14, T-15
T-17 + T-18 + T-19 → T-20 (E2E)
T-20 → T-21 (docs)
```

## Parallelization

- After T-1: T-2, T-3, T-4, T-16 in parallel
- After T-4: T-5, T-6 in parallel; T-7 (needs T-3 too)
- After T-7: T-8, T-9 in parallel; T-12
- After T-12: T-13, T-14, T-15 in parallel
- After T-16: T-17, T-18, T-19 in parallel (need respective API endpoints)
