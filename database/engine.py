"""Database engine and connection management."""

import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession, 
    async_sessionmaker,
    create_async_engine,
)

from config import get_settings
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self, database_url: str, echo: bool = False):
        """Initialize database manager.
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL queries
        """
        self.database_url = database_url
        self.echo = echo
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine, creating if necessary."""
        if self._engine is None:
            self._engine = create_async_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,  # Verify connections before use
            )
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory, creating if necessary."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._session_factory
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.exception("Failed to create database tables")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.exception("Failed to drop database tables")
            raise
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


@lru_cache()
def get_db_manager() -> DatabaseManager:
    """Get cached database manager instance."""
    settings = get_settings()
    return DatabaseManager(
        database_url=settings.database.url,
        echo=settings.database.echo,
    ) 