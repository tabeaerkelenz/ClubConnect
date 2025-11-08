import types

from tests.unit.utils import FakeSession
from app.services.club import create_club_service

class FakeClub:
    def __init__(self, id=1, name="FC Test", city="Berlin", sport="football"):
        self.id = id
        self.name = name
        self.city = city
        self.sport = sport

class FakeUser:
    def __init__(self, id=1, name="User1", email="user1@domain.com"):
        self.id = id
        self.name = name
        self.email = email

def test_create_club_happy_path(monkeypatch):
    db = FakeSession()
    user = FakeUser()
    payload = types.SimpleNamespace(
        model_dump=lambda **_: {
            "name": "FC Test",
            "description": "desc",
            "country": "DE",
            "city": "Berlin",
            "sport": "football",
            "founded_year": 2010
        }
    )

    calls = {}

    def fake_create_club(db_arg, **fields):
        calls["create_club"] = fields
        return FakeClub(id=1, name=fields["name"])

    def fake_add_membership(db_arg, user_id, club_id, role):
        calls["add_membership"] = (user_id, club_id, role)

    # Parch at the import site used by the service:
    monkeypatch.setattr("app.services.club.create_club", fake_create_club)
    monkeypatch.setattr("app.services.club.add_membership", fake_add_membership)

    club = create_club_service(db, payload, user)

    # asserts: side effects and output
    assert isinstance(club, FakeClub)
    assert club.name == "FC Test"
    assert club.id == 1
    assert db.commits == 1
    assert db.rollbacks == 0
    assert "create_club" in calls and calls["create_club"]["name"] == "FC Test"
    assert "add_membership" in calls and calls["add_membership"][0] == user.id


# permission path
def test_update_denied_if_not_owner(monkeypatch):
    db = FakeSession()
    user = FakeUser()
    data = types.SimpleNamespace(name="New Name")


