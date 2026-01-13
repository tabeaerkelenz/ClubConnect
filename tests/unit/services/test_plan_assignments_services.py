from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models.models import MembershipRole, PlanAssigneeRole
from app.services.plan_assignment import PlanAssignmentService
from app.repositories.plan_assignment import PlanAssignmentRepository
from app.services.membership import MembershipService
from app.schemas.plan_assignment import PlanAssigneeCreate
from app.exceptions.base import (
    NotClubMember,
    CoachOrOwnerRequiredError,
    PlanNotFoundError,
    PlanAssignmentExistsError,
    PlanAssigneeNotFound,
    UserNotClubMember,
)

from .factories import make_user


@pytest.fixture
def mock_plan_assignment_repo() -> MagicMock:
    return MagicMock(spec=PlanAssignmentRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def plan_assignment_service(mock_plan_assignment_repo: MagicMock, mock_membership_service: MagicMock) -> PlanAssignmentService:
    return PlanAssignmentService(repo=mock_plan_assignment_repo, membership_service=mock_membership_service)


def test_list_assignees_happy_path(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    club_id = 1
    plan_id = 10
    me = make_user(user_id=5)

    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    mock_plan_assignment_repo.list_for_plan.return_value = [MagicMock(), MagicMock()]

    # Act
    result = plan_assignment_service.list_assignees(club_id=club_id, plan_id=plan_id, me_id=me.id)

    # Assert
    assert len(result) == 2
    mock_membership_service.require_member_of_club.assert_called_once_with(me.id, club_id)
    mock_plan_assignment_repo.get_plan_in_club.assert_called_once_with(club_id=club_id, plan_id=plan_id)
    mock_plan_assignment_repo.list_for_plan.assert_called_once_with(plan_id=plan_id)


def test_list_assignees_propagates_not_member(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_membership_service.require_member_of_club.side_effect = NotClubMember()

    # Act / Assert
    with pytest.raises(NotClubMember):
        plan_assignment_service.list_assignees(club_id=1, plan_id=10, me_id=5)

    mock_plan_assignment_repo.get_plan_in_club.assert_not_called()
    mock_plan_assignment_repo.list_for_plan.assert_not_called()


def test_list_assignees_propagates_plan_not_found(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.side_effect = PlanNotFoundError()

    # Act / Assert
    with pytest.raises(PlanNotFoundError):
        plan_assignment_service.list_assignees(club_id=1, plan_id=10, me_id=5)

    mock_plan_assignment_repo.list_for_plan.assert_not_called()


def test_add_assignee_happy_path(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    club_id = 1
    plan_id = 10
    me = make_user(user_id=5)

    data = PlanAssigneeCreate(user_id=99, role=PlanAssigneeRole.athlete)

    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    created = MagicMock()
    mock_plan_assignment_repo.create_user_assignee.return_value = created

    # Act
    result = plan_assignment_service.add_assignee(club_id=club_id, plan_id=plan_id, me_id=me.id, data=data)

    # Assert
    assert result == created
    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(me.id, club_id)
    mock_plan_assignment_repo.get_plan_in_club.assert_called_once_with(club_id=club_id, plan_id=plan_id)
    mock_membership_service.require_member_of_club.assert_called_once_with(data.user_id, club_id)
    mock_plan_assignment_repo.create_user_assignee.assert_called_once()
    _, kwargs = mock_plan_assignment_repo.create_user_assignee.call_args
    assert kwargs["plan_id"] == plan_id
    assert kwargs["user_id"] == data.user_id
    assert kwargs["assigned_by_id"] == me.id


def test_add_assignee_propagates_guard_error(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_membership_service.require_coach_or_owner_of_club.side_effect = CoachOrOwnerRequiredError()
    data = PlanAssigneeCreate(user_id=99, role=PlanAssigneeRole.athlete)

    # Act / Assert
    with pytest.raises(CoachOrOwnerRequiredError):
        plan_assignment_service.add_assignee(club_id=1, plan_id=10, me_id=5, data=data)

    mock_plan_assignment_repo.get_plan_in_club.assert_not_called()
    mock_plan_assignment_repo.create_user_assignee.assert_not_called()


def test_add_assignee_rejects_target_user_not_member(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()

    # membership_service raises NotClubMember for missing membership
    mock_membership_service.require_member_of_club.side_effect = NotClubMember()
    data = PlanAssigneeCreate(user_id=99, role=PlanAssigneeRole.athlete)

    # Act / Assert
    with pytest.raises(UserNotClubMember):
        plan_assignment_service.add_assignee(club_id=1, plan_id=10, me_id=5, data=data)

    mock_plan_assignment_repo.create_user_assignee.assert_not_called()


def test_add_assignee_propagates_repo_conflict(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    mock_plan_assignment_repo.create_user_assignee.side_effect = PlanAssignmentExistsError()
    data = PlanAssigneeCreate(user_id=99, role=PlanAssigneeRole.athlete)

    # Act / Assert
    with pytest.raises(PlanAssignmentExistsError):
        plan_assignment_service.add_assignee(club_id=1, plan_id=10, me_id=5, data=data)


def test_remove_assignee_happy_path(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    club_id = 1
    plan_id = 10
    assignee_id = 123
    me = make_user(user_id=5)

    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    obj = MagicMock()
    obj.plan_id = plan_id
    mock_plan_assignment_repo.get.return_value = obj

    # Act
    plan_assignment_service.remove_assignee(club_id=club_id, plan_id=plan_id, assignee_id=assignee_id, me_id=me.id)

    # Assert
    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(me.id, club_id)
    mock_plan_assignment_repo.get_plan_in_club.assert_called_once_with(club_id=club_id, plan_id=plan_id)
    mock_plan_assignment_repo.get.assert_called_once_with(assignee_id=assignee_id)
    mock_plan_assignment_repo.delete.assert_called_once_with(obj)


def test_remove_assignee_raises_not_found_if_missing(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    mock_plan_assignment_repo.get.return_value = None

    # Act / Assert
    with pytest.raises(PlanAssigneeNotFound):
        plan_assignment_service.remove_assignee(club_id=1, plan_id=10, assignee_id=123, me_id=5)

    mock_plan_assignment_repo.delete.assert_not_called()


def test_remove_assignee_raises_not_found_if_wrong_plan(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.return_value = MagicMock()
    obj = MagicMock()
    obj.plan_id = 999  # mismatch
    mock_plan_assignment_repo.get.return_value = obj

    # Act / Assert
    with pytest.raises(PlanAssigneeNotFound):
        plan_assignment_service.remove_assignee(club_id=1, plan_id=10, assignee_id=123, me_id=5)

    mock_plan_assignment_repo.delete.assert_not_called()


def test_remove_assignee_propagates_plan_not_found(
    plan_assignment_service: PlanAssignmentService,
    mock_plan_assignment_repo: MagicMock,
):
    # Arrange
    mock_plan_assignment_repo.get_plan_in_club.side_effect = PlanNotFoundError()

    # Act / Assert
    with pytest.raises(PlanNotFoundError):
        plan_assignment_service.remove_assignee(club_id=1, plan_id=10, assignee_id=123, me_id=5)

    mock_plan_assignment_repo.get.assert_not_called()
    mock_plan_assignment_repo.delete.assert_not_called()
