import pytest

from tests.integration.conftest import _rand_email


# --- Happy paths ------------------------------------------------------------

def test_get_me_happy_path(client, auth_token, auth_headers):
    resp = client.get("/users/me", headers=auth_headers(auth_token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["id"]               # has id
    assert data["email"]            # has email


def test_update_me_change_name(client, auth_token, auth_headers):
    resp = client.patch(
        "/users/me",
        headers=auth_headers(auth_token),
        json={"name": "New Display Name"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "New Display Name"


def test_update_me_change_email_unique_ok(client, auth_token, auth_headers):
    """
    Adjust or remove if your API does NOT allow changing e-mail.
    """
    new_email = _rand_email("new")
    resp = client.patch(
        "/users/me",
        headers=auth_headers(auth_token),
        json={"email": new_email},
    )
    # If allowed, expect 200 and normalized (lowercased) e-mail in response.
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == new_email.lower()


# --- Constraints / negatives ------------------------------------------------

def test_me_requires_auth_401(client):
    assert client.get("/users/me").status_code == 401
    assert client.patch("/users/me", json={"name": "X"}).status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},                 # empty not allowed
        {"name": "A" * 256},          # too long (tune to your schema max length)
        {"email": "not-an-email"},    # invalid format
    ],
)
def test_update_me_validation_422(client, auth_token, payload, auth_headers):
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json=payload)
    assert resp.status_code == 422, resp.text


def test_update_me_conflict_email_409(client, auth_token, other_token, auth_headers):
    """
    If your DB enforces unique emails, trying to set my email to another user's email
    should yield 409.
    """
    # Read "other" user’s current e-mail from /users/me
    other_me = client.get("/users/me", headers=auth_headers(other_token)).json()
    taken_email = other_me["email"]

    resp = client.patch(
        "/users/me",
        headers=auth_headers(auth_token),
        json={"email": taken_email},
    )
    # If your service maps IntegrityError(unique) -> 409
    assert resp.status_code == 409, resp.text


def test_update_me_cannot_change_role_or_is_active(client, auth_token, auth_headers):
    """
    Your service should ignore or reject protected fields.
    Here we assert that changes to role/is_active do NOT take effect.
    Adjust assertions to match your actual behavior (200 and unchanged, or 422).
    """
    # Get current state
    me_before = client.get("/users/me", headers=auth_headers(auth_token)).json()
    before_role = me_before.get("role")
    before_active = me_before.get("is_active")

    # Try to change protected fields
    resp = client.patch(
        "/users/me",
        headers=auth_headers(auth_token),
        json={"role": "coach", "is_active": False},
    )

    # If you reject: assert resp.status_code == 422 (or 400)
    # If you ignore: expect 200 and no change in those fields
    assert resp.status_code in (200, 422, 400), resp.text

    # If your behavior is "ignore", keep these asserts; otherwise drop them.
    if resp.status_code == 200:
        me_after = resp.json()
        assert me_after.get("role") == before_role
        assert me_after.get("is_active") == before_active


def test_update_me_empty_body(client, auth_token, auth_headers):
    """
    Pick the behavior that matches your Pydantic model:
      - If UserUpdate requires at least one field -> expect 422
      - If empty allowed and returns current user -> expect 200
    """
    resp = client.patch("/users/me", headers=auth_headers(auth_token), json={})
    assert resp.status_code in (200, 422), resp.text
