"""Database utilities and session management for OpenGov Food."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Sequence

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..models.base import Base
from ..schemas.item import ItemCreate
from ..schemas.user import UserCreate
from .config import get_settings


def create_engine(echo: bool | None = None) -> AsyncEngine:
    """Create a configured AsyncEngine instance."""
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.DB_ECHO if echo is None else echo)


ENGINE: AsyncEngine = create_engine()
AsyncSessionLocal = async_sessionmaker(
    ENGINE, expire_on_commit=False, autoflush=False, autocommit=False
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session."""
    async with AsyncSessionLocal() as session:
        yield session


class DatabaseManager:
    """Database management utilities."""

    def __init__(self, engine: AsyncEngine | None = None):
        self.engine = engine or ENGINE
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False, autoflush=False, autocommit=False
        )

    async def initialize(self, drop_existing: bool = False) -> None:
        """Initialize the database schema."""
        async with self.engine.begin() as conn:
            if drop_existing:
                await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def seed_sample_data(self) -> None:
        """Seed database with sample data for demos and tests."""
        from ..crud.item import item as item_crud
        from ..crud.user import user as user_crud

        async with self.session_factory() as session:
            existing_users = await user_crud.get_multi(session, limit=1)
            if existing_users:
                return

            sample_users: Sequence[UserCreate] = [
                UserCreate(email="inspector@opengovfood.com", password="ChangeMe123", full_name="Inspector Example"),
                UserCreate(email="admin@opengovfood.com", password="ChangeMe123", full_name="Administrator Example", is_superuser=True),
            ]

            created_users = []
            for user_in in sample_users:
                created_users.append(await user_crud.create(session, obj_in=user_in))

            sample_items: Sequence[ItemCreate] = [
                ItemCreate(title="Weekly Inspection", description="Routine inspection workflow for downtown facilities"),
                ItemCreate(title="Temperature Compliance Review", description="Audit hot-holding equipment compliance"),
                ItemCreate(title="Consumer Complaint Investigation", description="Review complaint queue and follow-up actions"),
            ]

            owner_id = created_users[0].id
            for item_in in sample_items:
                await item_crud.create_with_owner(
                    session, obj_in=item_in, owner_id=owner_id
                )


def initialize_database_sync(drop_existing: bool = False) -> None:
    """Synchronously initialize the database, useful for CLI entrypoints."""

    async def _run() -> None:
        manager = DatabaseManager()
        await manager.initialize(drop_existing=drop_existing)

    asyncio.run(_run())


def seed_database_sync() -> None:
    """Synchronously seed the database with sample data."""

    async def _run() -> None:
        manager = DatabaseManager()
        await manager.seed_sample_data()

    asyncio.run(_run())