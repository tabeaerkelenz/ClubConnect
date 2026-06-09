import uuid
from unittest.mock import patch, MagicMock

from tests.helpers_auth import login_and_get_token, register_user
from app.schemas.workout_plan_ai import WorkoutPlanAIDraft, AIDraftItem, AIDraftExercise


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_workout_plan_payload(**overrides):
    return {"name": f"wp_{uuid.uuid4().hex[:6]}", "is_template": False, **overrides}


def _mk_item_payload(**overrides):
    return {"order_index": 0, "title": "Week 1 Day 1", **overrides}


def _mk_exercise_payload(**overrides):
    return {"name": "Squat", "sets": 3, "repetitions": 10, "position": 0, **overrides}


def _add_coach(client, auth_headers, owner_token, club_id):
    """Register a new user, add them as coach, return their token."""
    email = f"coach_{uuid.uuid4().hex[:6]}@example.com"
    register_user(client, email, "pw123456")
    token = login_and_get_token(client, email, "pw123456")
    client.post(
        f"/clubs/{club_id}/memberships",
        headers=auth_headers(owner_token),
        json={"email": email, "role": "coach"},
    )
    return token


def _add_member(client, auth_headers, owner_token, club_id):
    """Register a new user, add them as member, return their token."""
    email = f"member_{uuid.uuid4().hex[:6]}@example.com"
    register_user(client, email, "pw123456")
    token = login_and_get_token(client, email, "pw123456")
    client.post(
        f"/clubs/{club_id}/memberships",
        headers=auth_headers(owner_token),
        json={"email": email, "role": "member"},
    )
    return token


# ---------------------------------------------------------------------------
# Plans — list / create
# ---------------------------------------------------------------------------

def test_list_workout_plans_requires_membership(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    r = client.get(f"/clubs/{club_id}/workout-plans", headers=auth_headers(other_token))
    assert r.status_code == 403, r.text


def test_list_workout_plans_happy_path(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)

    r = client.get(f"/clubs/{club_id}/workout-plans", headers=auth_headers(owner_token))

    assert r.status_code == 200, r.text
    ids = [p["id"] for p in r.json()]
    assert created["id"] in ids


def test_create_workout_plan_happy_path(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)
    payload = _mk_workout_plan_payload(goal="Lose weight", duration_weeks=6)

    r = client.post(
        f"/clubs/{club_id}/workout-plans",
        headers=auth_headers(owner_token),
        json=payload,
    )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["club_id"] == club_id
    assert body["name"] == payload["name"]
    assert "created_by_id" in body


def test_create_workout_plan_requires_membership(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    r = client.post(
        f"/clubs/{club_id}/workout-plans",
        headers=auth_headers(other_token),
        json=_mk_workout_plan_payload(),
    )
    assert r.status_code == 403, r.text


# ---------------------------------------------------------------------------
# Plans — get (nested)
# ---------------------------------------------------------------------------

def test_get_workout_plan_nested_happy_path(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)

    r = client.get(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(owner_token),
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == created["id"]
    assert "items" in body


def test_get_workout_plan_not_found(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    r = client.get(f"/clubs/{club_id}/workout-plans/999999", headers=auth_headers(owner_token))
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# Plans — update
# ---------------------------------------------------------------------------

def test_update_workout_plan_by_owner(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(owner_token),
        json={"name": "Updated Name"},
    )

    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Updated Name"


def test_update_workout_plan_by_coach(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)
    coach_token = _add_coach(client, auth_headers, owner_token, club_id)

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(coach_token),
        json={"name": "Coach Updated"},
    )

    assert r.status_code == 200, r.text


def test_update_workout_plan_by_creator_member(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    member_token = _add_member(client, auth_headers, owner_token, club_id)
    # member creates their own plan
    created = workout_plan_factory(member_token, club_id)

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(member_token),
        json={"name": "My Updated Plan"},
    )

    assert r.status_code == 200, r.text


def test_update_workout_plan_denied_for_non_creator_member(
    client, auth_headers, owner_token, make_club_for_user, workout_plan_factory
):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)  # owner's plan
    member_token = _add_member(client, auth_headers, owner_token, club_id)

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(member_token),
        json={"name": "Sneaky Update"},
    )

    assert r.status_code == 403, r.text


# ---------------------------------------------------------------------------
# Plans — delete
# ---------------------------------------------------------------------------

def test_delete_workout_plan_by_owner(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)

    r = client.delete(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(owner_token),
    )
    assert r.status_code == 204, r.text

    r2 = client.get(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(owner_token),
    )
    assert r2.status_code == 404, r2.text


def test_delete_workout_plan_denied_for_non_creator_member(
    client, auth_headers, owner_token, make_club_for_user, workout_plan_factory
):
    club_id = make_club_for_user(owner_token)
    created = workout_plan_factory(owner_token, club_id)
    member_token = _add_member(client, auth_headers, owner_token, club_id)

    r = client.delete(
        f"/clubs/{club_id}/workout-plans/{created['id']}",
        headers=auth_headers(member_token),
    )
    assert r.status_code == 403, r.text


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def test_create_and_list_items(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)

    r = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(week_number=1),
    )
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["plan_id"] == plan["id"]

    r2 = client.get(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
    )
    assert r2.status_code == 200, r2.text
    assert any(i["id"] == item["id"] for i in r2.json())


def test_update_item(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)
    item_r = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(),
    )
    item_id = item_r.json()["id"]

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}",
        headers=auth_headers(owner_token),
        json={"title": "Updated Title"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Updated Title"


def test_delete_item(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)
    item_r = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(),
    )
    item_id = item_r.json()["id"]

    r = client.delete(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}",
        headers=auth_headers(owner_token),
    )
    assert r.status_code == 204, r.text


# ---------------------------------------------------------------------------
# Exercises
# ---------------------------------------------------------------------------

def test_create_and_list_exercises(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)
    item_r = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(),
    )
    item_id = item_r.json()["id"]

    r = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises",
        headers=auth_headers(owner_token),
        json=_mk_exercise_payload(),
    )
    assert r.status_code == 201, r.text
    ex = r.json()
    assert ex["name"] == "Squat"
    assert ex["item_id"] == item_id

    r2 = client.get(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises",
        headers=auth_headers(owner_token),
    )
    assert r2.status_code == 200, r2.text
    assert any(e["id"] == ex["id"] for e in r2.json())


def test_update_exercise(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)
    item_id = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(),
    ).json()["id"]
    ex_id = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises",
        headers=auth_headers(owner_token),
        json=_mk_exercise_payload(),
    ).json()["id"]

    r = client.patch(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises/{ex_id}",
        headers=auth_headers(owner_token),
        json={"sets": 5},
    )
    assert r.status_code == 200, r.text
    assert r.json()["sets"] == 5


def test_delete_exercise(client, auth_headers, owner_token, make_club_for_user, workout_plan_factory):
    club_id = make_club_for_user(owner_token)
    plan = workout_plan_factory(owner_token, club_id)
    item_id = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items",
        headers=auth_headers(owner_token),
        json=_mk_item_payload(),
    ).json()["id"]
    ex_id = client.post(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises",
        headers=auth_headers(owner_token),
        json=_mk_exercise_payload(),
    ).json()["id"]

    r = client.delete(
        f"/clubs/{club_id}/workout-plans/{plan['id']}/items/{item_id}/exercises/{ex_id}",
        headers=auth_headers(owner_token),
    )
    assert r.status_code == 204, r.text


# ---------------------------------------------------------------------------
# AI draft endpoint
# ---------------------------------------------------------------------------

def _mock_draft_json() -> str:
    draft = WorkoutPlanAIDraft(
        name="AI Strength Plan",
        description="AI generated",
        goal="Build strength",
        level="beginner",
        duration_weeks=4,
        items=[
            AIDraftItem(
                week_number=1,
                order_index=0,
                title="Day 1",
                exercises=[AIDraftExercise(name="Squat", sets=3, repetitions=10, position=0)],
            )
        ],
    )
    return draft.model_dump_json()


def test_ai_draft_requires_membership(client, auth_headers, owner_token, other_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    with patch("app.services.workout_plan_ai.OpenAI"):
        r = client.post(
            f"/clubs/{club_id}/workout-plans/ai-draft",
            headers=auth_headers(other_token),
            json={"goal": "Strength", "duration_weeks": 4, "days_per_week": 3},
        )
    assert r.status_code == 403, r.text


def test_ai_draft_happy_path(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    with patch("app.services.workout_plan_ai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.create.return_value.output_text = _mock_draft_json()

        r = client.post(
            f"/clubs/{club_id}/workout-plans/ai-draft",
            headers=auth_headers(owner_token),
            json={"goal": "Build strength", "duration_weeks": 4, "days_per_week": 3},
        )

    assert r.status_code == 201, r.text
    body = r.json()
    assert body["club_id"] == club_id
    assert "items" in body
    assert body["items"][0]["exercises"][0]["name"] == "Squat"


def test_ai_draft_rate_limit(client, auth_headers, owner_token, make_club_for_user):
    club_id = make_club_for_user(owner_token)

    with patch("app.services.workout_plan_ai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.create.return_value.output_text = _mock_draft_json()

        # Exhaust the 3-per-day quota
        payload = {"goal": "Strength", "duration_weeks": 1, "days_per_week": 1}
        for _ in range(3):
            client.post(
                f"/clubs/{club_id}/workout-plans/ai-draft",
                headers=auth_headers(owner_token),
                json=payload,
            )

        r = client.post(
            f"/clubs/{club_id}/workout-plans/ai-draft",
            headers=auth_headers(owner_token),
            json=payload,
        )

    assert r.status_code == 429, r.text
