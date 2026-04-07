"""SQLAlchemy 2.x models for the People of Interest database schema."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "persons"

    wikidata_id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    names_by_lang: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    article_titles: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(Text, nullable=True)
    occupations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    image_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender: Mapped[str | None] = mapped_column(Text, nullable=True)
    search_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_persons_category", "category"),
        Index(
            "ix_persons_search_text_trgm",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )


class PageviewDaily(Base):
    """Pageviews per person per language per day. Partitioned by month on date."""

    __tablename__ = "pageviews_daily"

    person_id: Mapped[str] = mapped_column(Text, primary_key=True)
    lang: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (date)"},
    )


class ScoreDaily(Base):
    """Pre-computed scores per person per day per window. Partitioned by month on date."""

    __tablename__ = "scores_daily"

    person_id: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    window: Mapped[str] = mapped_column("window", Text, primary_key=True)
    popularity: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    trending_zscore: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        {"postgresql_partition_by": "RANGE (date)"},
    )


class PipelineLog(Base):
    __tablename__ = "pipeline_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage: Mapped[str] = mapped_column(Text, nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
