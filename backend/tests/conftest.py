"""Tests run against a real PostgreSQL database (TEST_DATABASE_URL), migrated with Alembic."""
import os

TEST_DB = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://smartvocab:smartvocab@127.0.0.1:5433/smartvocab_test"
)
os.environ["DATABASE_URL"] = TEST_DB
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("AUTH_RATE_LIMIT_PER_MINUTE", "1000")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.rate_limit import reset_memory_limits  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

HERE = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    cfg = Config(os.path.join(HERE, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(HERE, "alembic"))
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    reset_memory_limits()
    yield
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))
    reset_memory_limits()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app, base_url="http://testserver")


PASSWORD = "sicheresPasswort1"


def register(client: TestClient, email: str = "anna@example.com", name: str = "Anna") -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD, "display_name": name})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    register(client)
    return client
