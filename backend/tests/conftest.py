import pytest_asyncio
import redis.asyncio as redis_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.db import Base, get_db
from app.core.redis import get_redis
from app.main import app

settings = get_settings()

# Tests get their own Postgres schema so they never touch the tables Alembic
# manages for real dev/prod data.
_TEST_SCHEMA = "test"
test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={"server_settings": {"search_path": _TEST_SCHEMA}},
)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)

_TEST_REDIS_URL = settings.redis_url.rsplit("/", 1)[0] + "/15"


async def _override_get_db():
    async with test_session_maker() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def _clean_state():
    async with test_engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {_TEST_SCHEMA}"))
        await conn.run_sync(Base.metadata.create_all)

    redis_client = redis_asyncio.from_url(_TEST_REDIS_URL, decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: redis_client

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await redis_client.flushdb()
    await redis_client.aclose()
    app.dependency_overrides.pop(get_redis, None)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
