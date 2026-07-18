from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# NullPool: asyncpg connections are bound to the event loop they were opened
# on, and pytest-asyncio gives each test function a fresh loop. A reused pool
# would hand back a connection tied to an already-closed loop.
engine = create_async_engine(settings.database_url, poolclass=NullPool)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session
