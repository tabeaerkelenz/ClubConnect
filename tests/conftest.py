import os
# must be before any app imports
os.environ.setdefault("SECRET_KEY", "test-secret")     # needed by JWT
os.environ.setdefault("ALGORITHM", "HS256")            # if your Settings requires it
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")  # if required
os.environ.setdefault("ENV", "test")                   # optional, if you have it

import uuid
import pytest
from datetime import datetime, timedelta, timezone

from app.db.database import build_session_maker
SQLITE_URL = "sqlite+pysqlite:///:memory:"
SessionMaker = build_session_maker(SQLITE_URL)

from app.db.deps import get_db


from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import event

from app.main import app
from app.db.database import build_session_maker
from app.db.models import  PlanType
from app.db.base import Base
from tests.helpers_auth import register_user, login_and_get_token  # you already use these

# ---- DB setup (SQLite :memory:) ----


@pytest.fixture(scope="session")
def _sqlite_sessionmaker():
    # Get the exact engine bound to this sessionmaker
    with SessionMaker() as s:
        engine = s.get_bind()

    # Enable FK constraints in SQLite
    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        try:
            dbapi_conn.execute("PRAGMA foreign_keys=ON;")
        except Exception:
            pass

    Base.metadata.create_all(bind=engine)

    yield SessionMaker

    # (Optional; in-memory DB goes away anyway once engine is gone)
    with SessionMaker() as s:
        engine = s.get_bind()
        Base.metadata.drop_all(bind=engine)

# tests/utils.py
@pytest.fixture
def db(_sqlite_sessionmaker):
    session = _sqlite_sessionmaker()
    try:
        yield session
    finally:
        try:
            if session.in_transaction():
                session.rollback()
        except Exception:
            pass
        session.expunge_all()
        session.close()

@pytest.fixture(scope="function")
def client(db: Session):
    # Override app's get_db to use our sqlite session
    def _override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# ---- Shared helpers (used by all suites) ----
@pytest.fixture
def auth_headers():
    def _mk(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _mk

@pytest.fixture
def rand_email():
    def _make(prefix: str = "u") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:6]}@example.com"
    return _make

# ---- Users ----
@pytest.fixture
def auth_token(client, rand_email):
    email = rand_email("me")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

@pytest.fixture
def owner_token(client, rand_email):
    email = rand_email("owner")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

@pytest.fixture
def other_token(client, rand_email):
    email = rand_email("other")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

# ---- Clubs ----
@pytest.fixture
def make_club_for_user(client, auth_headers):
    def _make(token, **overrides):
        payload = {
            "name": "testname",
            "country": "DE",
            "city": "Berlin",
            "sport": "football",
            "founded_year": 2010,
            "description": "Test club",
            **overrides,
        }
        resp = client.post("/clubs", headers=auth_headers(token), json=payload)
        assert resp.status_code in (201, 200), resp.text
        return resp.json()["id"]
    return _make

@pytest.fixture
def club_owned_by_someone_else(client, owner_token, auth_headers):
    payload = {"name": f"club_{uuid.uuid4().hex[:6]}"}
    resp = client.post("/clubs", headers=auth_headers(owner_token), json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]

# ---- Memberships ----
@pytest.fixture
def membership_factory(client, auth_headers):
    def _make(token: str, club_id: int, *, member_email: str, role: str = "member"):
        payload = {"email": member_email, "role": role}
        return client.post(
            f"/clubs/{club_id}/memberships",
            headers=auth_headers(token),
            json=payload,
        )
    return _make

@pytest.fixture
def self_join(client, auth_headers):
    """Return a function that joins the given token to the given club."""
    def _do(token: str, club_id: int):
        r = client.post(
            f"/clubs/{club_id}/memberships/join",
            headers=auth_headers(token),
        )
        assert r.status_code in (200, 201), r.text
        return r.json()
    return _do

# ---- Plans ----
@pytest.fixture
def rand_plan():
    def _make(prefix="plan"):
        return f"{prefix}_{uuid.uuid4().hex[:6]}"
    return _make

@pytest.fixture
def mk_plan_payload(rand_plan):
    def _make(*, plan_type: PlanType | str | None = None, name: str | None = None, description: str = "Test description long enough"):
        if plan_type is None:
            plan_type = getattr(PlanType, "training", list(PlanType)[0])
        if hasattr(plan_type, "value"):
            plan_type = plan_type.value
        return {
            "name": name or rand_plan("Plan"),
            "description": description,
            "plan_type": plan_type,
        }
    return _make


@pytest.fixture
def plan_factory(client, auth_headers, mk_plan_payload):
    def _make(token: str, club_id: int, payload: dict | None = None, plan_type: PlanType | str | None = None):
        payload = payload or mk_plan_payload(plan_type=plan_type)
        r = client.post(f"/clubs/{club_id}/plans", headers=auth_headers(token), json=payload)
        assert r.status_code in (200, 201), f"{r.status_code} -> {r.text} (payload={payload})"
        return r.json()
    return _make

# ---- Sessions ----
@pytest.fixture
def rand_session():
    def _make(prefix="sess"):
        return f"{prefix}_{uuid.uuid4().hex[:6]}"
    return _make

def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

@pytest.fixture
def mk_session_payload(rand_session):
    def _make(
    *,
    name: str | None = None,
    description: str | None = "Test session",
    starts_in_minutes: int = 60,
    duration_minutes: int = 90,
    location: str = "Pitch 1",
    note: str | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc)
        starts = now + timedelta(minutes=starts_in_minutes)
        ends = starts + timedelta(minutes=duration_minutes)
        return {
            "name": name or rand_session("Session"),
            "description": description,
            "starts_at": iso(starts),
            "ends_at": iso(ends),
            "location": location,
            "note": note,
        }
    return _make

@pytest.fixture
def mk_session_payload_invalid_time(rand_session):
    def _make():
        now = datetime.now(timezone.utc)
        starts = now + timedelta(hours=2)
        ends = now + timedelta(hours=1)
        return {
            "name": rand_session("Bad"),
            "description": "Invalid time",
            "starts_at": iso(starts),
            "ends_at": iso(ends),
            "location": "Pitch 1",
            "note": "bring water",
        }
    return _make

@pytest.fixture
def session_factory(client, auth_headers, mk_session_payload):
    def _make(token: str, club_id: int, plan_id: int, payload: dict | None = None):
        payload = payload or mk_session_payload()
        r = client.post(
            f"/clubs/{club_id}/plans/{plan_id}/sessions",
            headers=auth_headers(token),
            json=payload,
        )
        assert r.status_code in (200, 201), f"{r.status_code} -> {r.text} (payload={payload})"
        return r.json()
    return _make
