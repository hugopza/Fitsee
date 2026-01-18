import asyncio
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.core.database import get_db, Base
from app.core import security

# Use a test specific DB URL or just override the dependency
# For safety, let's presume we can run tests against the same postgres but maybe a different DB name?
# Or use SQLite? SQLite has issues with Postgres UUIDs.
# We will mock the get_db override to point to an in-memory or separate DB if possible.
# For this basic setup, assuming running inside Docker with a test DB is best.
# But to make it runnable easily, let's use the default URL but force a cleanup?
# SAFE OPTION: Use `sqlite+aiosqlite:///:memory:` but we need to patch UUID handling or use compatible types.
# Given the constraints, let's use the ENV variable TEST_DATABASE_URL if present, else warn.
# Actually, for the demo code, we'll configure it to use the main DB but usually you'd want isolation.
# Let's try to use valid logic for AsyncClient.

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    # If using local dev, this connects to localhost postgres.
    # WARNING: This might wipe data if we used the same DB. 
    # Ideally use a separate test DB.
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(db_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        # Rollback mainly handled by the fact we drop/create or just transaction rollback?
        # A simple approach for async tests is truncating tables or just relying on creation.
        # We did drop_all at start of session. Data persists across functions in this setup? 
        # No, we want isolation. 
        # Better: delete all data after each test.
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

@pytest.fixture(scope="function")
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    # Override generic get_db
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    
    app.dependency_overrides.clear()
