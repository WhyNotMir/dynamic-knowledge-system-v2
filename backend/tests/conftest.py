from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://dks:dks_secret@localhost:5432/dks_test",
    ),
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("UPLOAD_DIR", "/tmp/dks-rebuild-test-uploads")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", '["http://localhost:3000"]')

Path(os.environ["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

import app.models  # noqa: E402,F401
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        poolclass=NullPool,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Test database is unavailable: {exc}")

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    class FakeArqPool:
        def __init__(self) -> None:
            self.jobs: list[tuple[str, tuple]] = []

        async def enqueue_job(self, name: str, *args):
            self.jobs.append((name, args))

    app.dependency_overrides[get_db] = override_get_db
    app.state.arq_pool = FakeArqPool()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
