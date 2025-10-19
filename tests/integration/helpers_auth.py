from typing import Dict
from fastapi.testclient import TestClient

def register_user(client: TestClient, email: str, password: str, name: str = "Testy") -> Dict:
    r = client.post("/auth/register", json={"email": email, "password": password, "name": name})
    return r

def login_and_get_token(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
