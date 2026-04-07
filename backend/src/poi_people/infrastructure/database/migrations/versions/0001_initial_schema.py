"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-05

"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _month_range(start_date: date, count: int) -> list[tuple[str, str, str]]:
    """Generate (table_suffix, start, end) for count months starting from start_date's month."""
    results = []
    d = start_date.replace(day=1)
    for _ in range(count):
        suffix = d.strftime("%Y_%m")
        start = d.strftime("%Y-%m-%d")
        # advance to next month
        if d.month == 12:
            next_d = d.replace(year=d.year + 1, month=1)
        else:
            next_d = d.replace(month=d.month + 1)
        end = next_d.strftime("%Y-%m-%d")
        results.append((suffix, start, end))
        d = next_d
    return results


def upgrade() -> None:
    """Create all tables, extensions, indexes, trigger, and initial partitions."""

    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- persons table ---
    op.execute(sa.text("""
        CREATE TABLE persons (
            wikidata_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            names_by_lang JSONB NOT NULL DEFAULT '{}',
            article_titles JSONB NOT NULL DEFAULT '{}',
            category TEXT NOT NULL,
            birth_date DATE,
            death_date DATE,
            nationality TEXT,
            occupations JSONB,
            image_filename TEXT,
            gender TEXT,
            search_text TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """))

    # Indexes on persons
    op.execute("CREATE INDEX ix_persons_category ON persons USING btree (category)")
    op.execute("CREATE INDEX ix_persons_search_text_trgm ON persons USING gin (search_text gin_trgm_ops)")

    # Trigger function to populate search_text from name + names_by_lang values
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_person_search_text() RETURNS trigger AS $$
        DECLARE
            lang_values TEXT;
        BEGIN
            SELECT string_agg(value::text, ' ')
            INTO lang_values
            FROM jsonb_each_text(COALESCE(NEW.names_by_lang, '{}'::jsonb));

            NEW.search_text := COALESCE(NEW.name, '') || ' ' || COALESCE(lang_values, '');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    op.execute(sa.text("""
        CREATE TRIGGER trg_persons_search_text
        BEFORE INSERT OR UPDATE ON persons
        FOR EACH ROW EXECUTE FUNCTION update_person_search_text()
    """))

    # --- pageviews_daily (partitioned) ---
    op.execute(sa.text("""
        CREATE TABLE pageviews_daily (
            person_id TEXT NOT NULL,
            lang TEXT NOT NULL,
            date DATE NOT NULL,
            views INTEGER NOT NULL,
            PRIMARY KEY (person_id, lang, date)
        ) PARTITION BY RANGE (date)
    """))

    # --- scores_daily (partitioned) ---
    op.execute(sa.text("""
        CREATE TABLE scores_daily (
            person_id TEXT NOT NULL,
            date DATE NOT NULL,
            "window" TEXT NOT NULL,
            popularity BIGINT,
            trending_zscore DOUBLE PRECISION,
            PRIMARY KEY (person_id, date, "window")
        ) PARTITION BY RANGE (date)
    """))

    # Composite indexes on scores_daily for top-N queries
    op.execute('CREATE INDEX ix_scores_daily_trending_zscore ON scores_daily ("window", date, trending_zscore DESC)')
    op.execute('CREATE INDEX ix_scores_daily_popularity ON scores_daily ("window", date, popularity DESC)')

    # --- pipeline_log ---
    op.execute(sa.text("""
        CREATE TABLE pipeline_log (
            id SERIAL PRIMARY KEY,
            stage TEXT NOT NULL,
            run_date DATE NOT NULL,
            status TEXT NOT NULL,
            started_at TIMESTAMPTZ NOT NULL,
            finished_at TIMESTAMPTZ,
            record_count INTEGER,
            error_detail TEXT,
            metadata JSONB
        )
    """))

    # Create partitions: current month + 4 future months
    today = date.today()
    partitions = _month_range(today, 5)

    for suffix, start, end in partitions:
        op.execute(sa.text(
            f"CREATE TABLE pageviews_daily_{suffix} PARTITION OF pageviews_daily "
            f"FOR VALUES FROM ('{start}') TO ('{end}')"
        ))
        op.execute(sa.text(
            f"CREATE TABLE scores_daily_{suffix} PARTITION OF scores_daily "
            f"FOR VALUES FROM ('{start}') TO ('{end}')"
        ))


def downgrade() -> None:
    """Drop all tables, trigger, and extensions."""
    op.execute("DROP TABLE IF EXISTS pipeline_log CASCADE")
    op.execute("DROP TABLE IF EXISTS scores_daily CASCADE")
    op.execute("DROP TABLE IF EXISTS pageviews_daily CASCADE")
    op.execute("DROP TRIGGER IF EXISTS trg_persons_search_text ON persons")
    op.execute("DROP FUNCTION IF EXISTS update_person_search_text()")
    op.execute("DROP TABLE IF EXISTS persons CASCADE")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm CASCADE")
