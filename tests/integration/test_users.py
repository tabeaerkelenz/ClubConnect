import pytest

# --- Happy paths ------------------------------------------------------------

def test_get_me_happy_path(client, auth_token, auth_headers):
    resp = client.get("/users/me", headers=auth_headers(auth_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"]
    assert data["email"]

def test_update_me_change_name(client, auth_token, auth_headers):
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json={"name": "New Display Name"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "New Display Name"

def test_update_me_change_email_unique_ok(client, auth_token, auth_headers, rand_email):
    new_email = rand_email("new")
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json={"email": new_email})
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == new_email.lower()

# --- Constraints / negatives ------------------------------------------------

def test_me_requires_auth_401(client):
    assert client.get("/users/me").status_code == 401
    assert client.patch("/users/me", json={"name": "X"}).status_code == 401

@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "A" * 256},
        {"email": "not-an-email"},
    ],
)
def test_update_me_validation_422(client, auth_token, payload, auth_headers):
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json=payload)
    assert resp.status_code == 422, resp.text

def test_update_me_conflict_email_409(client, auth_token, other_token, auth_headers):
    other_me = client.get("/users/me", headers=auth_headers(other_token)).json()
    taken_email = other_me["email"]

    resp = client.patch("/users/me", headers=auth_headers(auth_token), json={"email": taken_email})
    assert resp.status_code == 409, resp.text

def test_update_me_cannot_change_role_or_is_active(client, auth_token, auth_headers):
    me_before = client.get("/users/me", headers=auth_headers(auth_token)).json()
    before_role = me_before.get("role")
    before_active = me_before.get("is_active")

    resp = client.patch(
        "/users/me",
        headers=auth_headers(auth_token),
        json={"role": "coach", "is_active": False},
    )
    assert resp.status_code in (200, 422, 400), resp.text
    if resp.status_code == 200:
        me_after = resp.json()
        assert me_after.get("role") == before_role
        assert me_after.get("is_active") == before_active

def test_update_me_empty_body(client, auth_token, auth_headers):
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json={})
    assert resp.status_code in (200, 422), resp.text
