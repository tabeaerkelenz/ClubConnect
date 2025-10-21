import pytest

# Happy paths
def test_club_create_happy_path(client, auth_token, auth_headers):
    payload = {
        "name": "FC Example",
        "description": "An example football club.",
        "country": "DE",
        "city": "Example City",
        "sports_type": "Football",
        "founded_year": 1900,
    }
    resp = client.post("/clubs", headers=auth_headers(auth_token), json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "FC Example"
    assert "id" in data

def test_club_get_by_id_happy_path(client, auth_token, auth_headers):
    resp = client.post("/clubs", headers=auth_headers(auth_token), json={"name": "One"})
    club_id = resp.json()["id"]

    resp = client.get(f"/clubs/{club_id}", headers=auth_headers(auth_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == club_id

def test_club_list_happy_path(client, auth_token, auth_headers):
    client.post("/clubs", headers=auth_headers(auth_token), json={"name": "Listable"})
    resp = client.get("/clubs", headers=auth_headers(auth_token))
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert len(ids) >= 1

def test_club_search_happy_path(client, auth_token, auth_headers):
    client.post("/clubs", headers=auth_headers(auth_token), json={"name": "Searchable FC"})
    resp = client.get("/clubs?q=Searchable", headers=auth_headers(auth_token))
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert any(name == "Searchable FC" for name in names)

def test_club_delete_happy_path(client, auth_token, auth_headers):
    resp = client.post("/clubs", headers=auth_headers(auth_token), json={"name": "Deletable"})
    club_id = resp.json()["id"]

    resp = client.delete(f"/clubs/{club_id}", headers=auth_headers(auth_token))
    assert resp.status_code == 204

    resp = client.get(f"/clubs/{club_id}", headers=auth_headers(auth_token))
    assert resp.status_code == 404

def test_club_get_my_clubs_happy_path(client, auth_token, auth_headers):
    resp = client.post("/clubs", headers=auth_headers(auth_token), json={"name": "My Club"})
    club_id = resp.json()["id"]

    resp = client.get("/clubs/mine", headers=auth_headers(auth_token))
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert club_id in ids

def test_owner_can_update_club(client, auth_token, make_club_for_user, auth_headers):
    club_id = make_club_for_user(token=auth_token)
    resp = client.patch(
        f"/clubs/{club_id}",
        headers=auth_headers(auth_token),
        json={"name": "New Name", "city": "Berlin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New Name"
    assert body["city"] == "Berlin"

def test_partial_update_preserves_fields(client, auth_token, auth_headers, make_club_for_user):
    club_id = make_club_for_user(auth_token, name="Club X", city="Munich")
    r = client.patch(f"/clubs/{club_id}", headers=auth_headers(auth_token), json={"name": "Y Club"})
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Y Club"
    assert data["city"] == "Munich"

def test_create_sets_owner_membership(client, auth_token, auth_headers):
    r = client.post("/clubs", headers=auth_headers(auth_token), json={"name": "OwnerFC"})
    assert r.status_code in (200, 201)
    # Wenn es einen Endpoint wie /clubs/mine gibt:
    mine = client.get("/clubs/mine", headers=auth_headers(auth_token)).json()
    assert any(c["name"] == "OwnerFC" for c in mine)


# Constraints / negative cases
def test_club_create_requires_auth_401(client):
    resp = client.post("/clubs", json={"name": "Nope"})
    assert resp.status_code == 401

def test_my_clubs_empty(client, auth_token, auth_headers):
    r = client.get("/clubs/mine", headers=auth_headers(auth_token))
    assert r.status_code == 200
    assert r.json() == []

def test_club_get_unknown_id_404(client, auth_token, auth_headers):
    resp = client.get("/clubs/999999", headers=auth_headers(auth_token))
    assert resp.status_code == 404

def test_club_search_no_results(client, auth_token, auth_headers):
    resp = client.get("/clubs?q=NonExistentClubName", headers=auth_headers(auth_token))
    assert resp.status_code == 200
    assert resp.json() == []

@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"name": ""}, 422),
        ({"name": "A" * 256}, 422),
        ({}, 422),
    ],
)
def test_club_create_validation_422(client, auth_token, auth_headers, payload, expected):
    resp = client.post("/clubs", headers=auth_headers(auth_token), json=payload)
    assert resp.status_code == expected

@pytest.mark.parametrize("body", [{"name": ""}, {"name": "A"*256}])
def test_update_validation_422(client, auth_token, auth_headers, make_club_for_user, body):
    club_id = make_club_for_user(auth_token)
    r = client.patch(f"/clubs/{club_id}", headers=auth_headers(auth_token), json=body)
    assert r.status_code == 422

def test_non_owner_cannot_update_club(client, other_token, club_owned_by_someone_else, auth_headers):
    resp = client.patch(
        f"/clubs/{club_owned_by_someone_else}",
        headers=auth_headers(other_token),
        json={"name": "Hacked"},
    )
    assert resp.status_code in (403, 404)

def test_non_owner_cannot_delete_club(client, other_token, club_owned_by_someone_else, auth_headers):
    r = client.delete(f"/clubs/{club_owned_by_someone_else}", headers=auth_headers(other_token))
    assert r.status_code in (403, 404)