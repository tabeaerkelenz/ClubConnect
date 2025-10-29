from tests.helpers_auth import register_user, login_and_get_token, auth_headers

PASSWORD1 = "pw123456"


# ---------- AUTH: REGISTER ----------

def test_register_returns_token_201(client):
    email = rand_email()
    r = register_user(client, email, PASSWORD1, name="Alice")
    assert r.status_code == 201, r.text
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"

def test_register_duplicate_email_409(client):
    email = rand_email()
    r1 = register_user(client, email, PASSWORD1, name="Bob")
    assert r1.status_code == 201
    r2 = register_user(client, email, "pw678900", name="Bobby")
    assert r2.status_code == 409, r2.text

# ---------- AUTH: LOGIN ----------

def test_login_success_and_get_me(client):
    email = rand_email()
    register_user(client, email, PASSWORD1, name="Cara")
    token = login_and_get_token(client, email, PASSWORD1)
    me = client.get("/users/me", headers=auth_headers(token))
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email

def test_login_wrong_password_401(client):
    email = rand_email()
    register_user(client, email, PASSWORD1)
    r = client.post("/auth/login", data={"username": email, "password": "wrong"})
    assert r.status_code == 401, r.text

# ---------- USERS: /users/me ----------

def test_me_requires_token_401(client):
    r = client.get("/users/me")
    assert r.status_code in (401, 403), r.text

def test_update_me_allows_name_and_email(client):
    email = rand_email()
    register_user(client, email, PASSWORD1, name="Old Name")
    token = login_and_get_token(client, email, PASSWORD1)
    hdrs = auth_headers(token)

    # change name + email, expect normalization (lowercase)
    new_email = rand_email().upper()
    r = client.patch("/users/me", headers=hdrs, json={"name": "New Name", "email": new_email})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "New Name"
    assert body["email"] == new_email.lower()

def test_update_me_rejects_taken_email_409(client):
    # user A
    a_email = rand_email("user_a")
    register_user(client, a_email, PASSWORD1)
    a_token = login_and_get_token(client, a_email, PASSWORD1)

    # user B
    b_email = rand_email("user_b")
    register_user(client, b_email, PASSWORD1)
    b_token = login_and_get_token(client, b_email, PASSWORD1)

    # B tries to set email = A's email -> 409
    r = client.patch("/users/me", headers=auth_headers(b_token), json={"email": a_email})
    assert r.status_code == 409, r.text


def test_change_password_flow(client):
    email = rand_email()
    register_user(client, email, "oldpw123")
    token = login_and_get_token(client, email, "oldpw123")
    hdrs = auth_headers(token)

    # change password
    r = client.post("/auth/me/password", headers=hdrs, json={"old_password": "oldpw123", "new_password": "newpw123"})
    assert r.status_code in (200, 204), r.text

    # old fails, new works
    r_old = client.post("/auth/login", data={"username": email, "password": "oldpw123"})
    assert r_old.status_code == 401
    r_new = client.post("/auth/login", data={"username": email, "password": "newpw123"})
    assert r_new.status_code == 200


# to run tests: ../.venv/bin/python -m pytest -q tests/integration/test_auth_users.py
