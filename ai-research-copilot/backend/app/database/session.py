"""
Database session management.

Provides async database session factory and dependency injection.
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database.async_database_url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_pre_ping=True,
    echo=settings.debug,
)

# Create session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Yields:
        AsyncSession: Database session for request handling.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _ensure_schema(conn) -> None:
    """Ensure database schema is up-to-date for development.

    Adds missing columns to existing tables without dropping data.
    """
    # Check if conversation_id column exists on documents table
    result = await conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'documents' AND column_name = 'conversation_id'"
        )
    )
    if result.fetchone() is None:
        logger.info("Adding conversation_id column to documents table...")
        await conn.execute(
            text(
                "ALTER TABLE documents ADD COLUMN conversation_id "
                "UUID REFERENCES conversations(id) ON DELETE SET NULL"
            )
        )
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_documents_conversation_id ON documents(conversation_id)")
        )
        logger.info("Schema migration complete.")


async def init_db() -> None:
    """Initialize database tables.

    In development, creates all tables directly and applies missing columns.
    In production, expects Alembic migrations to have been run.
    """
    from app.core.config import settings
    if settings.env != "production":
        async with engine.begin() as conn:
            from app.database.base import Base
            # Import all models to register them with Base
            import app.models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
            # Apply any missing columns
            await _ensure_schema(conn)


async def close_db() -> None:
    """Close database engine connections."""
    await engine.dispose()
