import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker, Session

from app.db.deps import get_db

# 1) Point to a *real* Postgres test DB (container, CI var, etc.)
PG_URL = os.environ.get("DATABASE_URL", "")
if not PG_URL or PG_URL.startswith("sqlite"):
    pytest.skip(
        "Skipping integration tests: Postgres DATABASE_URL not set.",
        allow_module_level=True,
    )

from app.main import app
from app.db.database import build_session_maker

# 2) Migrate to head (once per session)
@pytest.fixture(scope="session", autouse=True)
def _migrate_db():
    # Run Alembic upgrade head here, or ensure CI did it.
    # Example (pseudo):
    # from alembic.config import Config
    # from alembic import command
    # cfg = Config("alembic.ini")
    # command.upgrade(cfg, "head")
    pass

@pytest.fixture(scope="session")
def _pg_sessionmaker() -> sessionmaker:
    return build_session_maker(PG_URL)

@pytest.fixture
def db(_pg_sessionmaker) -> Session:
    session = _pg_sessionmaker()
    tx = session.begin()
    try:
        yield session
    finally:
        tx.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db: Session):
    def _override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
