from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool


def _test_database_url() -> str:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return explicit

    current = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://dks:dks_secret@localhost:5432/dks_db",
    )
    return make_url(current).set(database="dks_test").render_as_string(hide_password=False)


os.environ["DATABASE_URL"] = _test_database_url()
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("UPLOAD_DIR", "/tmp/dks-rebuild-test-uploads")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", '["http://localhost:3000"]')

Path(os.environ["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

import app.models  # noqa: E402,F401
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def test_engine():
    await _ensure_test_database_exists(os.environ["DATABASE_URL"])

    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        poolclass=NullPool,
    )

    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.execute(text("DROP TABLE IF EXISTS article_block_embeddings"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Test database is unavailable: {exc}")

    yield engine

    await engine.dispose()


async def _ensure_test_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database
    if not database_name or not database_name.endswith("_test"):
        raise RuntimeError(f"Refusing to run tests against non-test database: {database_name}")

    admin_url = url.set(database="postgres")
    admin_engine = create_async_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    quoted_database_name = database_name.replace('"', '""')

    try:
        async with admin_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            )
            if exists is None:
                await conn.execute(text(f'CREATE DATABASE "{quoted_database_name}"'))
    finally:
        await admin_engine.dispose()


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
