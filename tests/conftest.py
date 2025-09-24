from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from opengovfood.api import deps
from opengovfood.core.database import Base
from opengovfood.web.app import app

TEST_DATABASE_URI = "sqlite+aiosqlite:///:memory:"

environment_engine = create_async_engine(
    TEST_DATABASE_URI,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(environment_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> AsyncIterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def database_schema() -> AsyncIterator[None]:
    async with environment_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with environment_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def client() -> AsyncIterator[TestClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[deps.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
async def async_client() -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[deps.get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()


@pytest.fixture
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    from tests.utils.utils import get_superuser_token_headers

    return get_superuser_token_headers(client)
