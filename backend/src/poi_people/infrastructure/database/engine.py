"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def get_database_url() -> str:
    """Read the database URL from the environment.

    Returns:
        The DATABASE_URL environment variable value.

    Raises:
        RuntimeError: If DATABASE_URL is not set.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return url


def create_engine(url: str | None = None, *, echo: bool = False):
    """Create an async SQLAlchemy engine.

    Args:
        url: Database URL. If None, reads from DATABASE_URL env var.
        echo: Whether to log SQL statements.

    Returns:
        An AsyncEngine instance.
    """
    db_url = url or get_database_url()
    return create_async_engine(
        db_url,
        echo=echo,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine.

    Args:
        engine: An AsyncEngine instance.

    Returns:
        An async_sessionmaker that produces AsyncSession instances.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
