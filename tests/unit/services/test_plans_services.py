from unittest.mock import MagicMock

import pytest

from app.services.plan import PlanService
from app.repositories.plan import PlanRepository
from app.services.membership import MembershipService
from app.schemas.plan import PlanCreate, PlanUpdate
from app.exceptions.base import (
    NotClubMember,
    NotCoachOfClubError,
    PlanNotFoundError,
    PlanNameExistsError,
)
from app.models.models import PlanAssigneeRole, Plan, PlanType, User
from .factories import make_user


@pytest.fixture
def me() -> User:
    return make_user(user_id=42)


@pytest.fixture
def mock_plan_repo() -> MagicMock:
    return MagicMock(spec=PlanRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def plan_service(
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
) -> PlanService:
    return PlanService(
        plan_repo=mock_plan_repo,
        membership_service=mock_membership_service,
    )


# ---------------------------------------------------------------------------
# list_plans_for_club
# ---------------------------------------------------------------------------

def test_list_plans_for_club_checks_membership_and_calls_repo(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    mock_plans = [MagicMock(spec=Plan), MagicMock(spec=Plan)]
    mock_plan_repo.list_plans_for_club.return_value = mock_plans

    result = plan_service.list_plans_for_club(club_id=club_id, me=me)

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )
    mock_plan_repo.list_plans_for_club.assert_called_once_with(club_id=club_id)
    assert result == mock_plans


def test_list_plans_for_club_raises_if_not_member(
    plan_service: PlanService,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    mock_membership_service.require_member_of_club.side_effect = NotClubMember

    with pytest.raises(NotClubMember):
        plan_service.list_plans_for_club(club_id=club_id, me=me)


# ---------------------------------------------------------------------------
# list_assigned_plans
# ---------------------------------------------------------------------------

def test_list_assigned_plans_member_check_and_repo_call_with_role_enum(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    role_str = "coach"
    mock_plans = [MagicMock(spec=Plan)]
    mock_plan_repo.list_assigned_plans.return_value = mock_plans

    result = plan_service.list_assigned_plans(
        club_id=club_id,
        me=me,
        role=role_str,
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )

    mock_plan_repo.list_assigned_plans.assert_called_once_with(
        club_id=club_id,
        user_id=me.id,
        role=PlanAssigneeRole.coach,
    )

    assert result == mock_plans


def test_list_assigned_plans_with_no_role_passes_none(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    mock_plans = [MagicMock(spec=Plan)]
    mock_plan_repo.list_assigned_plans.return_value = mock_plans

    result = plan_service.list_assigned_plans(
        club_id=club_id,
        me=me,
        role=None,
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )

    mock_plan_repo.list_assigned_plans.assert_called_once_with(
        club_id=club_id,
        user_id=me.id,
        role=None,
    )

    assert result == mock_plans


def test_list_assigned_plans_invalid_role_returns_empty_list_and_skips_repo(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    role_str = "banana"

    result = plan_service.list_assigned_plans(
        club_id=club_id,
        me=me,
        role=role_str,
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )
    mock_plan_repo.list_assigned_plans.assert_not_called()
    assert result == []


# ---------------------------------------------------------------------------
# get_plan
# ---------------------------------------------------------------------------

def test_get_plan_checks_membership_and_uses_repo(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 10
    plan = MagicMock(spec=Plan)
    mock_plan_repo.get_plan_in_club.return_value = plan

    result = plan_service.get_plan(club_id=club_id, plan_id=plan_id, me=me)

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )
    mock_plan_repo.get_plan_in_club.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
    )
    assert result == plan


def test_get_plan_propagates_plan_not_found(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 99
    mock_plan_repo.get_plan_in_club.side_effect = PlanNotFoundError

    with pytest.raises(PlanNotFoundError):
        plan_service.get_plan(club_id=club_id, plan_id=plan_id, me=me)

    mock_membership_service.require_member_of_club.assert_called_once()


# ---------------------------------------------------------------------------
# create_plan
# ---------------------------------------------------------------------------

def test_create_plan_requires_membership_and_calls_repo(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    data = PlanCreate(name="Plan A", plan_type=PlanType.club, description=None)
    plan = MagicMock(spec=Plan)
    mock_plan_repo.create_plan.return_value = plan

    result = plan_service.create_plan(club_id=club_id, me=me, data=data)

    mock_membership_service.require_member_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )

    mock_plan_repo.create_plan.assert_called_once_with(
        club_id=club_id,
        created_by_id=me.id,
        data=data,
    )

    assert result == plan


def test_create_plan_propagates_plan_name_exists(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    data = PlanCreate(name="Duplicate", plan_type=PlanType.club, description=None)
    mock_plan_repo.create_plan.side_effect = PlanNameExistsError

    with pytest.raises(PlanNameExistsError):
        plan_service.create_plan(club_id=club_id, me=me, data=data)

    mock_membership_service.require_member_of_club.assert_called_once()


def test_create_plan_raises_if_not_member(
    plan_service: PlanService,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    data = PlanCreate(name="Plan A", plan_type=PlanType.club, description=None)
    mock_membership_service.require_member_of_club.side_effect = (
        NotClubMember
    )

    with pytest.raises(NotClubMember):
        plan_service.create_plan(club_id=club_id, me=me, data=data)


# ---------------------------------------------------------------------------
# update_plan
# ---------------------------------------------------------------------------

def test_update_plan_fetches_then_updates(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 10
    data = PlanUpdate(name="New Name")
    plan = MagicMock(spec=Plan)
    updated = MagicMock(spec=Plan)
    mock_plan_repo.get_plan_in_club.return_value = plan
    mock_plan_repo.update_plan.return_value = updated

    result = plan_service.update_plan(
        club_id=club_id,
        plan_id=plan_id,
        me=me,
        data=data,
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )
    mock_plan_repo.get_plan_in_club.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
    )
    mock_plan_repo.update_plan.assert_called_once_with(
        plan=plan,
        data=data,
    )

    assert result == updated


def test_update_plan_propagates_plan_not_found(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 999
    data = PlanUpdate(name="New Name")

    mock_plan_repo.get_plan_in_club.side_effect = PlanNotFoundError

    with pytest.raises(PlanNotFoundError):
        plan_service.update_plan(
            club_id=club_id,
            plan_id=plan_id,
            me=me,
            data=data,
        )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once()


def test_update_plan_raises_if_not_coach_or_owner(
    plan_service: PlanService,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 10
    data = PlanUpdate(name="New Name")

    mock_membership_service.require_coach_or_owner_of_club.side_effect = (
        NotCoachOfClubError
    )

    with pytest.raises(NotCoachOfClubError):
        plan_service.update_plan(
            club_id=club_id,
            plan_id=plan_id,
            me=me,
            data=data,
        )


# ---------------------------------------------------------------------------
# delete_plan
# ---------------------------------------------------------------------------

def test_delete_plan_fetches_then_deletes(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 10
    plan = MagicMock(spec=Plan)
    mock_plan_repo.get_plan_in_club.return_value = plan

    plan_service.delete_plan(club_id=club_id, plan_id=plan_id, me=me)

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        user_id=me.id,
        club_id=club_id,
    )
    mock_plan_repo.get_plan_in_club.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
    )
    mock_plan_repo.delete_plan.assert_called_once_with(plan=plan)


def test_delete_plan_propagates_plan_not_found(
    plan_service: PlanService,
    mock_plan_repo: MagicMock,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 999
    mock_plan_repo.get_plan_in_club.side_effect = PlanNotFoundError

    with pytest.raises(PlanNotFoundError):
        plan_service.delete_plan(club_id=club_id, plan_id=plan_id, me=me)

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once()


def test_delete_plan_raises_if_not_coach_or_owner(
    plan_service: PlanService,
    mock_membership_service: MagicMock,
    me: User,
):
    club_id = 1
    plan_id = 10

    mock_membership_service.require_coach_or_owner_of_club.side_effect = (
        NotCoachOfClubError
    )

    with pytest.raises(NotCoachOfClubError):
        plan_service.delete_plan(club_id=club_id, plan_id=plan_id, me=me)
