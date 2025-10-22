import uuid
import pytest

from tests.integration.conftest import _rand_email
from tests.integration.helpers_auth import register_user, login_and_get_token


# ---------- LIST ----------
def test_list_memberships_requires_membership(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    # other_token ist nicht Member dieses Clubs → 403
    resp = client.get(f"/clubs/{club_id}/memberships", headers=auth_headers(other_token))
    assert resp.status_code == 403, resp.text

def test_list_memberships_happy_path(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    resp = client.get(f"/clubs/{club_id}/memberships", headers=auth_headers(owner_token))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    # Club-Creator sollte als Coach/Owner Mitglied sein (je nach Implementierung mind. 1 Eintrag)
    assert isinstance(rows, list)
    assert len(rows) >= 1
    assert all("id" in r and "role" in r and "club_id" in r for r in rows)


# ---------- /memberships/mine ----------
def test_my_memberships_returns_all(client, auth_headers, owner_token, other_token, make_club_for_user):
    # owner ist in zwei Clubs Mitglied; /memberships/mine sollte beide liefern
    club_a = make_club_for_user(owner_token)
    club_b = make_club_for_user(owner_token)
    resp = client.get("/memberships/mine", headers=auth_headers(owner_token))
    assert resp.status_code == 200, resp.text
    clubs = {m["club_id"] for m in resp.json()}
    assert {club_a, club_b}.issubset(clubs)


# ---------- POST add_membership ----------
def test_add_membership_happy_path(client, auth_headers, owner_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    email = _rand_email("member")
    register_user(client, email, "pw123456")
    resp = membership_factory(owner_token, club_id, member_email=email, role="member")
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["club_id"] == club_id
    assert body["role"] == "member"

def test_add_membership_unknown_email_404(client, auth_headers, owner_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    resp = membership_factory(owner_token, club_id, member_email="does-not-exist@example.com", role="member")
    assert resp.status_code in (400, 404), resp.text  # dein _map_crud_errors -> 404 empfohlen

def test_add_membership_conflict_409(client, auth_headers, owner_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    email = _rand_email("member")
    register_user(client, email, "pw123456")
    # first add
    first = membership_factory(owner_token, club_id, member_email=email, role="member")
    assert first.status_code in (200, 201), first.text
    # second add
    second = membership_factory(owner_token, club_id, member_email=email, role="member")
    assert second.status_code == 409, second.text

def test_add_membership_requires_coach_403(client, auth_headers, owner_token, other_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    # other_token is not coach
    email = _rand_email("member")
    register_user(client, email, "pw123456")
    resp = membership_factory(other_token, club_id, member_email=email, role="member")
    assert resp.status_code == 403, resp.text


# ---------- POST /join (self_join) ----------
def test_self_join_happy_path(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    # other_token can join
    resp = client.post(f"/clubs/{club_id}/memberships/join", headers=auth_headers(other_token))
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["club_id"] == club_id
    assert body["role"] == "member"

def test_self_join_conflict_if_already_member(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    # join 1
    r1 = client.post(f"/clubs/{club_id}/memberships/join", headers=auth_headers(other_token))
    assert r1.status_code in (200, 201), r1.text
    # join 2 -> 409
    r2 = client.post(f"/clubs/{club_id}/memberships/join", headers=auth_headers(other_token))
    assert r2.status_code == 409, r2.text


# ---------- PATCH /{membership_id}/role ----------
def test_change_role_to_coach_by_coach(client, auth_headers, owner_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    # create member
    email = _rand_email("member")
    register_user(client, email, "pw123456")
    created = membership_factory(owner_token, club_id, member_email=email, role="member").json()
    membership_id = created["id"]

    # change role
    payload = {"role": "coach"}
    resp = client.patch(
        f"/clubs/{club_id}/memberships/{membership_id}/role",
        headers=auth_headers(owner_token),
        json=payload,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == "coach"

def test_change_role_requires_coach_403(client, auth_headers, owner_token, other_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)
    # owner adds user a
    email = _rand_email("member")
    register_user(client, email, "pw123456")
    created = membership_factory(owner_token, club_id, member_email=email, role="member").json()
    membership_id = created["id"]

    payload = {"role": "coach"}
    resp = client.patch(
        f"/clubs/{club_id}/memberships/{membership_id}/role",
        headers=auth_headers(other_token),
        json=payload,
    )
    assert resp.status_code == 403, resp.text

def test_change_role_404_for_unknown_membership(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    payload = {"role": "coach"}
    resp = client.patch(
        f"/clubs/{club_id}/memberships/999999/role",
        headers=auth_headers(owner_token),
        json=payload,
    )
    assert resp.status_code == 404 or resp.status_code == 400, resp.text  # je nach Service


# ---------- DELETE /{membership_id} ----------
def _get_memberships(client, token, club_id, auth_headers):
    r = client.get(f"/clubs/{club_id}/memberships", headers=auth_headers(token))
    assert r.status_code == 200, r.text
    return r.json()

def test_member_can_remove_self(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    # other joins
    j = client.post(f"/clubs/{club_id}/memberships/join", headers=auth_headers(other_token))
    assert j.status_code in (200, 201), j.text
    member_id = j.json()["id"]

    # self-delete accepted → 204
    d = client.delete(f"/clubs/{club_id}/memberships/{member_id}", headers=auth_headers(other_token))
    assert d.status_code == 204, d.text

    # verify member is gone
    members = _get_memberships(client, owner_token, club_id, auth_headers)
    assert all(m["id"] != member_id for m in members)

def test_noncoach_cannot_remove_other_member(client, auth_headers, owner_token, other_token, make_club_for_user, membership_factory):
    club_id = make_club_for_user(owner_token)

    # A (other_token) joint self, B gets added
    j = client.post(f"/clubs/{club_id}/memberships/join", headers=auth_headers(other_token))
    assert j.status_code in (200, 201), j.text

    email_b = _rand_email("memberb")
    register_user(client, email_b, "pw123456")
    created_b = membership_factory(owner_token, club_id, member_email=email_b, role="member").json()

    # other_token try to delete b → 403 (no coach not self)
    d = client.delete(
        f"/clubs/{club_id}/memberships/{created_b['id']}",
        headers=auth_headers(other_token),
    )
    assert d.status_code == 403, d.text

def test_cannot_remove_last_coach_of_club(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    # get Coach-Membership (of Owners)
    rows = _get_memberships(client, owner_token, club_id, auth_headers)
    owner_membership = next((m for m in rows if m["role"] in ("coach", "owner") or m["user_id"] == rows[0]["user_id"]), rows[0])
    # try, delete last coach → 400 (LastCoachViolationError)
    resp = client.delete(
        f"/clubs/{club_id}/memberships/{owner_membership['id']}",
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 400, resp.text
