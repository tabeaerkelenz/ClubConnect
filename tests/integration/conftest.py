import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.integration.fixtures_auth import signup_and_login


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient):
    return signup_and_login(client)