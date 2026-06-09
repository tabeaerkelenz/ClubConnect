from unittest.mock import MagicMock

import pytest

from app.services.workout_plan import WorkoutPlanService
from app.services.membership import MembershipService
from app.repositories.workout_plan import WorkoutPlanRepository
from app.models.models import Membership, MembershipRole, WorkoutPlan
from app.exceptions.base import CoachOrOwnerRequiredError, WorkoutNotFoundError
from .factories import make_membership


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock(spec=WorkoutPlanRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def svc(mock_repo, mock_membership_service) -> WorkoutPlanService:
    return WorkoutPlanService(repo=mock_repo, membership_service=mock_membership_service)


def make_plan(plan_id: int = 1, club_id: int = 10, created_by_id: int = 42):
    plan = MagicMock(spec=WorkoutPlan)
    plan.id = plan_id
    plan.club_id = club_id
    plan.created_by_id = created_by_id
    return plan


# ---------------------------------------------------------------------------
# list_plans
# ---------------------------------------------------------------------------

def test_list_plans_requires_membership_then_calls_repo(svc, mock_repo, mock_membership_service):
    mock_repo.list_plans.return_value = []

    result = svc.list_plans(club_id=10, user_id=42)

    mock_membership_service.require_member_of_club.assert_called_once_with(club_id=10, user_id=42)
    mock_repo.list_plans.assert_called_once_with(10)
    assert result == []


def test_list_plans_propagates_membership_error(svc, mock_membership_service):
    from app.exceptions.base import NotClubMember
    mock_membership_service.require_member_of_club.side_effect = NotClubMember

    with pytest.raises(NotClubMember):
        svc.list_plans(club_id=10, user_id=99)


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------

def test_create_plan_requires_membership_and_passes_creator(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=42)
    mock_repo.create_plan.return_value = plan
    data = {"name": "My Plan", "is_template": False}

    result = svc.create_plan(club_id=10, user_id=42, data=data)

    mock_membership_service.require_member_of_club.assert_called_once_with(club_id=10, user_id=42)
    mock_repo.create_plan.assert_called_once_with(club_id=10, created_by_id=42, data=data)
    assert result is plan


# ---------------------------------------------------------------------------
# get_plan
# ---------------------------------------------------------------------------

def test_get_plan_flat_calls_get_plan(svc, mock_repo, mock_membership_service):
    plan = make_plan()
    mock_repo.get_plan.return_value = plan

    result = svc.get_plan(club_id=10, plan_id=1, user_id=42, nested=False)

    mock_membership_service.require_member_of_club.assert_called_once_with(club_id=10, user_id=42)
    mock_repo.get_plan.assert_called_once_with(club_id=10, plan_id=1)
    mock_repo.get_plan_nested.assert_not_called()
    assert result is plan


def test_get_plan_nested_calls_get_plan_nested(svc, mock_repo, mock_membership_service):
    plan = make_plan()
    mock_repo.get_plan_nested.return_value = plan

    result = svc.get_plan(club_id=10, plan_id=1, user_id=42, nested=True)

    mock_repo.get_plan_nested.assert_called_once_with(club_id=10, plan_id=1)
    mock_repo.get_plan.assert_not_called()
    assert result is plan


def test_get_plan_propagates_not_found(svc, mock_repo, mock_membership_service):
    mock_repo.get_plan.side_effect = WorkoutNotFoundError

    with pytest.raises(WorkoutNotFoundError):
        svc.get_plan(club_id=10, plan_id=999, user_id=42)


# ---------------------------------------------------------------------------
# update_plan — permission matrix
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("role", [MembershipRole.coach, MembershipRole.owner])
def test_update_plan_allowed_for_coach_and_owner(role, svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)  # someone else's plan
    updated = make_plan()
    mock_repo.get_plan.return_value = plan
    mock_repo.update_plan.return_value = updated
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=role
    )

    result = svc.update_plan(club_id=10, plan_id=1, user_id=42, patch={"name": "New"})

    mock_repo.update_plan.assert_called_once_with(club_id=10, plan_id=1, patch={"name": "New"})
    assert result is updated


def test_update_plan_allowed_for_plan_creator(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=42)  # user IS the creator
    updated = make_plan()
    mock_repo.get_plan.return_value = plan
    mock_repo.update_plan.return_value = updated
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )

    result = svc.update_plan(club_id=10, plan_id=1, user_id=42, patch={"name": "Mine"})

    mock_repo.update_plan.assert_called_once()
    assert result is updated


def test_update_plan_denied_for_member_who_is_not_creator(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)  # different user owns the plan
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )

    with pytest.raises(CoachOrOwnerRequiredError):
        svc.update_plan(club_id=10, plan_id=1, user_id=42, patch={"name": "Nope"})

    mock_repo.update_plan.assert_not_called()


# ---------------------------------------------------------------------------
# delete_plan
# ---------------------------------------------------------------------------

def test_delete_plan_allowed_for_coach(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.coach
    )

    svc.delete_plan(club_id=10, plan_id=1, user_id=42)

    mock_repo.delete_plan.assert_called_once_with(club_id=10, plan_id=1)


def test_delete_plan_denied_for_non_creator_member(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )

    with pytest.raises(CoachOrOwnerRequiredError):
        svc.delete_plan(club_id=10, plan_id=1, user_id=42)

    mock_repo.delete_plan.assert_not_called()


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

def test_list_items_requires_membership(svc, mock_repo, mock_membership_service):
    mock_repo.list_items.return_value = []

    result = svc.list_items(club_id=10, plan_id=1, user_id=42)

    mock_membership_service.require_member_of_club.assert_called_once_with(club_id=10, user_id=42)
    mock_repo.list_items.assert_called_once_with(club_id=10, plan_id=1)
    assert result == []


def test_create_item_allowed_for_coach(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    item = MagicMock()
    mock_repo.get_plan.return_value = plan
    mock_repo.create_item.return_value = item
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.coach
    )
    data = {"title": "Week 1 Monday", "order_index": 0}

    result = svc.create_item(club_id=10, plan_id=1, user_id=42, data=data)

    mock_repo.create_item.assert_called_once_with(club_id=10, plan_id=1, data=data)
    assert result is item


def test_create_item_denied_for_non_creator_member(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )

    with pytest.raises(CoachOrOwnerRequiredError):
        svc.create_item(club_id=10, plan_id=1, user_id=42, data={"order_index": 0})

    mock_repo.create_item.assert_not_called()


def test_delete_item_allowed_for_owner(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.owner
    )

    svc.delete_item(club_id=10, plan_id=1, item_id=5, user_id=42)

    mock_repo.delete_item.assert_called_once_with(club_id=10, plan_id=1, item_id=5)


# ---------------------------------------------------------------------------
# Exercises
# ---------------------------------------------------------------------------

def test_list_exercises_requires_membership(svc, mock_repo, mock_membership_service):
    mock_repo.list_exercises.return_value = []

    svc.list_exercises(club_id=10, plan_id=1, item_id=5, user_id=42)

    mock_membership_service.require_member_of_club.assert_called_once_with(club_id=10, user_id=42)
    mock_repo.list_exercises.assert_called_once_with(club_id=10, plan_id=1, item_id=5)


def test_create_exercise_allowed_for_plan_creator(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=42)
    ex = MagicMock()
    mock_repo.get_plan.return_value = plan
    mock_repo.create_exercise.return_value = ex
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )
    data = {"name": "Squat", "sets": 3, "repetitions": 10, "position": 0}

    result = svc.create_exercise(club_id=10, plan_id=1, item_id=5, user_id=42, data=data)

    mock_repo.create_exercise.assert_called_once_with(club_id=10, plan_id=1, item_id=5, data=data)
    assert result is ex


def test_delete_exercise_denied_for_non_creator_member(svc, mock_repo, mock_membership_service):
    plan = make_plan(created_by_id=99)
    mock_repo.get_plan.return_value = plan
    mock_membership_service.get_membership_for_user_in_club.return_value = make_membership(
        membership_id=1, club_id=10, user_id=42, role=MembershipRole.member
    )

    with pytest.raises(CoachOrOwnerRequiredError):
        svc.delete_exercise(club_id=10, plan_id=1, item_id=5, exercise_id=7, user_id=42)

    mock_repo.delete_exercise.assert_not_called()
