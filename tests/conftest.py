import uuid
import pytest
import psycopg2
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import database.unit_of_work as uow_module
import services.client_service as client_svc
import services.product_service as product_svc
import services.order_service as order_svc
import services.auth_service as auth_svc
from core.config import settings
from app.main import app


TEST_DB_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@localhost:{settings.DB_PORT}/{settings.DB_NAME}"
)
TEST_DB_SYNC_URL = (
    f"postgresql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@localhost:{settings.DB_PORT}/{settings.DB_NAME}"
)


class FakeRedis:
    async def get(self, key): return None
    async def set(self, key, value, ex=None): pass
    async def keys(self, pattern): return []
    async def delete(self, *keys): pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    orig = uow_module.async_session_maker
    uow_module.async_session_maker = session_maker

    fake = FakeRedis()
    client_svc.redis_client = fake
    product_svc.redis_client = fake
    order_svc.redis_client = fake
    auth_svc.redis_client = fake

    yield
    uow_module.async_session_maker = orig


@pytest.fixture
def client():
    return TestClient(app)


def _db_execute(sql, params):
    conn = psycopg2.connect(TEST_DB_SYNC_URL)
    conn.cursor().execute(sql, params)
    conn.commit()
    conn.close()


@pytest.fixture
def new_client(client):
    payload = {
        "name": "Bohdan",
        "email": f"user_{uuid.uuid4().hex[:8]}@gmail.com",
        "password": "pass123",
        "age": 25,
    }
    client.post("/auth/register", json=payload)
    _db_execute("UPDATE clients SET is_verified=true WHERE email=%s", (payload["email"],))
    return payload


@pytest.fixture
def auth_headers(client, new_client):
    response = client.post("/auth/client_login", data={
        "username": new_client["email"],
        "password": new_client["password"],
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
