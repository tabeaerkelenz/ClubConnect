import uuid

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.integration.helpers_auth import register_user, login_and_get_token


# ---------------- Fixtures ----------------

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers():
    def _mk(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
    return _mk

def _rand_email(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:6]}@example.com"

@pytest.fixture
def auth_token(client):
    email = _rand_email("me")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

@pytest.fixture
def owner_token(client):
    email = _rand_email("owner")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

@pytest.fixture
def other_token(client):
    email = _rand_email("other")
    register_user(client, email, "pw123456")
    return login_and_get_token(client, email, "pw123456")

@pytest.fixture
def make_club_for_user(client, auth_headers):
    """Create a club via API using the caller's token. Return the new club id."""
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
    """Create a club owned by *owner_token* and return its id."""
    payload = {"name": f"club_{uuid.uuid4().hex[:6]}"}  # add fields if your API requires them
    resp = client.post("/clubs", headers=auth_headers(owner_token), json=payload)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]