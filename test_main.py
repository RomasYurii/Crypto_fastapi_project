import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from main import app, get_db
from database import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(engine_test, expire_on_commit=False)

@pytest.fixture(scope="function")
async def db_session():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_currency(client):
    response = await client.get("/currency/bitcoin")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "bitcoin"
    assert "id" in data


@pytest.mark.asyncio
async def test_history(client):
    await client.get("/currency/bitcoin")
    response = await client.get("/history")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    first_record = data[0]
    assert "id" in first_record
    assert "symbol" in first_record
    assert "price_usd" in first_record
    assert "fetched_at" in first_record

    assert first_record["symbol"] == "bitcoin"
