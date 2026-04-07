# Requirements: People of Interest

## Summary

A web application that surfaces trending and popular people worldwide by aggregating Wikipedia pageview data across multiple language editions. Displays results in a ranked table with profile images, names linked to Wikipedia articles, and popularity/trending scores. Uses the same Wikimedia pageview dump data (stored in S3) as the Points of Interest project, but focused on biographical entities (Wikidata P31=Q5, human).

## User Stories

- As a **curious user**, I want to see which people are attracting unusual attention right now so I can discover who's in the news without reading the news.
- As a **researcher**, I want to compare popularity of people across different Wikipedia language editions to understand cultural attention differences.

## Functional Requirements

### Data Ingestion — Person Registry

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-001 | Maintain a registry of notable people (Wikidata items with P31=Q5 and at least one Wikipedia sitelink in the configured language editions) | Must Have | MVP |
| FR-002 | For each person, store: Wikidata ID, name, names by language, article titles by language, date of birth (P569), date of death (P577 if applicable), nationality (P27), occupation/categories (P106), gender (P21), image URL (P18 via Wikimedia Commons) | Must Have | MVP |
| FR-003 | Classify each person by category using Wikidata P106 (occupation) mapped to display categories: politician, athlete, artist/entertainer, scientist/academic, business, writer, historical figure, other | Must Have | MVP |
| FR-004 | Refresh the person registry weekly from Wikidata dumps | Must Have | MVP |
| FR-005 | Reuse pageview dump files from the S3 bucket (`s3://poi-pageview-dumps/pageviews/`) — do not re-download from Wikimedia | Must Have | MVP |

### Data Ingestion — Pageview Data

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-006 | Ingest daily pageview counts for configured Wikipedia language editions, reading dump files from S3 | Must Have | MVP |
| FR-007 | Resolve each pageview record to a person in the registry by matching article titles | Must Have | MVP |
| FR-008 | Store raw pageview counts per person per language per day | Must Have | MVP |

### Data Processing — Scoring

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-009 | Compute daily popularity score per person based on total cross-language pageview volume | Must Have | MVP |
| FR-010 | Compute trending scores using Z-score over rolling 30-day mean | Must Have | MVP |
| FR-011 | Support configurable time windows: daily / weekly / monthly | Must Have | MVP |
| FR-012 | Compute year-over-year comparison when >12 months of history exist | Should Have | MVP |

### Frontend — Table Display

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-013 | Display a ranked table of people sorted by the selected score (popularity or trending) | Must Have | MVP |
| FR-014 | Each table row shows: rank, profile thumbnail (from Wikidata P18/Wikimedia Commons, fallback to placeholder), name as hyperlink to Wikipedia article, category badge, score value, sparkline mini-chart (last 7 days) | Must Have | MVP |
| FR-015 | Table supports pagination (50 rows per page) with total count | Must Have | MVP |
| FR-016 | Profile images loaded from Wikimedia Commons via the Special:FilePath API. Lazy-loaded for performance | Must Have | MVP |

### Frontend — Controls

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-017 | View toggle: trending (default) / popularity | Must Have | MVP |
| FR-018 | Time window selector: daily / weekly / monthly | Must Have | MVP |
| FR-019 | Category filter: multi-select for person categories (politician, athlete, etc.) | Must Have | MVP |
| FR-020 | Language edition selector: choose which Wikipedia editions contribute to the score. Default: English | Must Have | MVP |
| FR-021 | Date picker: select which day's data to display. Default: latest available | Must Have | MVP |
| FR-022 | Search by person name — filters the table and highlights matching rows | Must Have | MVP |
| FR-023 | Sort by any column (rank, name, category, score) | Must Have | MVP |

### Frontend — Person Detail

| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| FR-024 | Clicking a person row expands an inline detail section or opens a side panel showing: full name, larger photo, birth/death dates, nationality, occupation list, Wikipedia links for all language editions, sparkline chart (30 days / 12 weeks / 12 months matching window), language breakdown bar chart | Must Have | MVP |
| FR-025 | Link to Wikipedia article opens in new tab | Must Have | MVP |

## Non-Functional Requirements

### Performance
| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| NFR-001 | Table renders initial 50 rows within 2 seconds | Must Have | MVP |
| NFR-002 | Pagination loads next page within 500ms | Must Have | MVP |
| NFR-003 | Profile images lazy-loaded, table usable before images finish loading | Must Have | MVP |

### Data Quality
| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| NFR-004 | All profile image URLs validated — broken images show placeholder | Must Have | MVP |
| NFR-005 | Person categories cover >90% of notable people (measured by pageview volume) | Must Have | MVP |

### Deployment
| ID | Requirement | Priority | Phase |
|----|-------------|----------|-------|
| NFR-006 | Deployable via Docker Compose | Must Have | MVP |
| NFR-007 | Shares S3 bucket with Points of Interest project for pageview dumps | Must Have | MVP |
| NFR-008 | Structured logging for all pipeline stages | Must Have | MVP |

## Edge Cases

- EC-1: Person with article in only 1 language edition — score still computes correctly
- EC-2: Person with no image on Wikidata — show placeholder avatar
- EC-3: Living person vs historical figure — both handled, death date nullable
- EC-4: Person with multiple P106 occupations — classify by primary (first listed)
- EC-5: Very recently created Wikipedia article — insufficient history handled gracefully

## Acceptance Criteria

- [ ] AC-1: Table displays top 50 people ranked by popularity with profile images
- [ ] AC-2: Category filter correctly filters to selected occupation types
- [ ] AC-3: Language selector changes score calculations (e.g., Japanese Wikipedia shows different top people than English)
- [ ] AC-4: Clicking a person shows detail with sparkline and language breakdown
- [ ] AC-5: Profile images load from Wikimedia Commons without CORS errors
- [ ] AC-6: Search finds people by name across languages
- [ ] AC-7: Date picker constrains to available data range
- [ ] AC-8: Pageview data sourced from S3 bucket, not re-downloaded from Wikimedia

## Out of Scope

- Map visualization (that's the Points of Interest project)
- Social media data
- Real-time streaming (daily granularity sufficient)
- User accounts or personalization
- Mobile-native apps
