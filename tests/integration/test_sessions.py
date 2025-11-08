# ---------- tests: list & get ----------


def test_list_sessions_happy_path(client, auth_headers, owner_token, make_club_for_user, plan_factory, session_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])

    r = client.get(f"/clubs/{club_id}/plans/{plan['id']}/sessions", headers=auth_headers(owner_token))
    assert r.status_code == 200, r.text
    items = r.json()
    assert isinstance(items, list) and any(s["id"] == created["id"] for s in items)

def test_get_session_by_id_happy_path(client, auth_headers, owner_token, make_club_for_user, plan_factory, session_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])
    r = client.get(f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}", headers=auth_headers(owner_token))
    assert r.status_code == 200, r.text
    assert r.json()["id"] == created["id"]

def test_list_sessions_requires_membership_403(client, auth_headers, owner_token, other_token, make_club_for_user, plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    r = client.get(f"/clubs/{club_id}/plans/{plan['id']}/sessions", headers=auth_headers(other_token))
    assert r.status_code == 403, r.text

def test_get_session_404_for_unknown(client, auth_headers, owner_token, make_club_for_user, plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    r = client.get(f"/clubs/{club_id}/plans/{plan['id']}/sessions/999999", headers=auth_headers(owner_token))
    assert r.status_code == 404, r.text


# ---------- tests: create ----------

def test_create_session_by_coach_ok(client, auth_headers, owner_token, make_club_for_user, plan_factory, mk_session_payload):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    payload = mk_session_payload()
    r = client.post(f"/clubs/{club_id}/plans/{plan['id']}/sessions", headers=auth_headers(owner_token), json=payload)
    assert r.status_code in (200, 201), f"{r.status_code} -> {r.text}"

def test_create_session_forbidden_for_member_non_coach(client, auth_headers, owner_token, other_token, make_club_for_user, plan_factory, mk_session_payload, self_join):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    self_join(other_token, club_id)  # member, not coach
    r = client.post(f"/clubs/{club_id}/plans/{plan['id']}/sessions", headers=auth_headers(other_token), json=mk_session_payload())
    assert r.status_code == 403, f"{r.status_code} -> {r.text}"

def test_create_session_422_invalid_time_range(client, auth_headers, owner_token, make_club_for_user, plan_factory, mk_session_payload_invalid_time):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    r = client.post(f"/clubs/{club_id}/plans/{plan['id']}/sessions", headers=auth_headers(owner_token), json=mk_session_payload_invalid_time())
    assert r.status_code == 422, f"{r.status_code} -> {r.text}"


# ---------- tests: update ----------

def test_update_session_by_coach_ok(client, auth_headers, owner_token, make_club_for_user, plan_factory, session_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])
    patch = {"description": "Updated desc"}
    r = client.patch(
        f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}",
        headers=auth_headers(owner_token),
        json=patch,
    )
    assert r.status_code == 200, f"{r.status_code} -> {r.text}"
    body = r.json()
    assert body["id"] == created["id"]
    if "description" in body:
        assert body["description"] == patch["description"]

def test_update_session_forbidden_for_member_non_coach(client, auth_headers, owner_token, other_token, make_club_for_user, plan_factory, session_factory, self_join,
                                                       rand_session):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])
    self_join(other_token, club_id)
    r = client.patch(
        f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}",
        headers=auth_headers(other_token),
        json={"name": rand_session("TryUpdate")},
    )
    assert r.status_code == 403, f"{r.status_code} -> {r.text}"


# ---------- tests: delete ----------

def test_delete_session_by_coach_ok(client, auth_headers, owner_token, make_club_for_user, plan_factory, session_factory):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])
    r = client.delete(
        f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}",
        headers=auth_headers(owner_token),
    )
    assert r.status_code == 204, f"{r.status_code} -> {r.text}"
    # verify gone
    r2 = client.get(f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}", headers=auth_headers(owner_token))
    assert r2.status_code == 404, f"{r2.status_code} -> {r2.text}"

def test_delete_session_forbidden_for_member_non_coach(client, auth_headers, owner_token, other_token, make_club_for_user, plan_factory, session_factory, self_join):
    club_id = make_club_for_user(owner_token)
    plan = plan_factory(owner_token, club_id)
    created = session_factory(owner_token, club_id, plan["id"])
    self_join(other_token, club_id)
    r = client.delete(
        f"/clubs/{club_id}/plans/{plan['id']}/sessions/{created['id']}",
        headers=auth_headers(other_token),
    )
    assert r.status_code == 403, f"{r.status_code} -> {r.text}"
