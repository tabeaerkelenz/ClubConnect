import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, Session

from app.db.deps import get_db
from app.main import app
from app.db.database import build_session_maker

# 1) Point to a *real* Postgres test DB (container, CI var, etc.)
PG_URL = os.environ.get("DATABASE_URL", "")
if not PG_URL or PG_URL.startswith("sqlite"):
    pytest.skip(
        "Skipping integration tests: Postgres DATABASE_URL not set.",
        allow_module_level=True,
    )

@pytest.fixture(scope="session")
def _pg_sessionmaker() -> sessionmaker:
    return build_session_maker(PG_URL)

# Migrate to head (once per session)
@pytest.fixture(scope="session", autouse=True)
def _migrate_db():
    # Run Alembic upgrade head here, or ensure CI did it.
    # Example (pseudo):
    # from alembic.config import Config
    # from alembic import command
    # cfg = Config("alembic.ini")
    # command.upgrade(cfg, "head")
    pass


@pytest.fixture
def db(_pg_sessionmaker) -> Generator[Session, None, None]:

    session = _pg_sessionmaker()

    # outer transaction stays open for the whole test
    outer = session.begin()

    # use SAVEPOINT for nested transactions (to allow rollback)
    nested = session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        # stats a new savepoint so next test is isolated as well
        # only if a nested transaction (savepoint) ends
        if trans.nested and not sess.in_nested_transaction():
            sess.begin_nested()

    try:
        yield session
    finally:
        try:
            if nested.is_active:
                nested.rollback()
        except Exception:
            pass
        try:
            if outer.is_active:
                outer.rollback()
        except Exception:
            pass
        session.close()


@pytest.fixture(scope="function")
def client(db: Session):
    # app should use exactly this session
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
