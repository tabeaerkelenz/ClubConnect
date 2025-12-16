from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.services.attendance import AttendanceService
from app.repositories.attendance import AttendanceRepository
from app.services.membership import MembershipService
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from app.exceptions.base import (
    CoachOrOwnerRequiredError,
    NotClubMember,
    InvalidTimeRange,
    AttendanceExistsError,
    AttendanceNotFoundError,
)

from factories import make_user


@pytest.fixture
def mock_attendance_repo() -> MagicMock:
    return MagicMock(spec=AttendanceRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def attendance_service(mock_attendance_repo: MagicMock, mock_membership_service: MagicMock) -> AttendanceService:
    return AttendanceService(attendance_repo=mock_attendance_repo, membership_service=mock_membership_service)


def test_create_happy_path_calls_guards_and_repo(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    club_id = 1
    session_id = 10
    user_id = 99
    me = make_user(user_id=7)

    payload = AttendanceCreate(
        status=None,  # should default in service
        checked_in_at=None,
        checked_out_at=None,
        note="hello",
    )

    created = MagicMock()
    mock_attendance_repo.create.return_value = created

    # Act
    result = attendance_service.create(
        club_id=club_id,
        session_id=session_id,
        user_id=user_id,
        me_id=me.id,
        data=payload,
    )

    # Assert
    assert result == created
    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(me.id, club_id)
    mock_membership_service.require_member_of_club.assert_called_once_with(user_id, club_id)

    mock_attendance_repo.create.assert_called_once()
    _, kwargs = mock_attendance_repo.create.call_args
    assert kwargs["session_id"] == session_id
    assert kwargs["user_id"] == user_id
    assert kwargs["recorded_by_id"] == me.id
    assert kwargs["note"] == "hello"
    assert kwargs["status"] is not None  # service sets a default


def test_create_raises_invalid_time_range(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
):
    # Arrange
    ci = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    co = datetime(2025, 1, 1, 9, 0, tzinfo=timezone.utc)
    payload = AttendanceCreate(checked_in_at=ci, checked_out_at=co, note=None, status=None)

    # Act / Assert
    with pytest.raises(InvalidTimeRange):
        attendance_service.create(club_id=1, session_id=1, user_id=2, me_id=3, data=payload)

    mock_attendance_repo.create.assert_not_called()


def test_create_propagates_guard_error(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_membership_service.require_coach_or_owner_of_club.side_effect = CoachOrOwnerRequiredError()

    # Act / Assert
    with pytest.raises(CoachOrOwnerRequiredError):
        attendance_service.create(club_id=1, session_id=1, user_id=2, me_id=3, data=AttendanceCreate())

    mock_attendance_repo.create.assert_not_called()


def test_create_propagates_target_not_member(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    mock_membership_service.require_member_of_club.side_effect = NotClubMember()

    # Act / Assert
    with pytest.raises(NotClubMember):
        attendance_service.create(club_id=1, session_id=1, user_id=2, me_id=3, data=AttendanceCreate())

    mock_attendance_repo.create.assert_not_called()


def test_create_propagates_repo_error(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
):
    # Arrange
    mock_attendance_repo.create.side_effect = AttendanceExistsError()

    # Act / Assert
    with pytest.raises(AttendanceExistsError):
        attendance_service.create(club_id=1, session_id=1, user_id=2, me_id=3, data=AttendanceCreate())

    mock_attendance_repo.create.assert_called_once()


def test_list_by_session_happy_path(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    me = make_user(user_id=5)
    mock_attendance_repo.list_by_session_in_club.return_value = [MagicMock(), MagicMock()]

    # Act
    result = attendance_service.list_by_session(club_id=1, session_id=10, me_id=me.id, skip=0, limit=50)

    # Assert
    assert len(result) == 2
    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(me.id, 1)
    mock_attendance_repo.list_by_session_in_club.assert_called_once_with(club_id=1, session_id=10, skip=0, limit=50)


def test_get_happy_path(
    attendance_service: AttendanceService,
    mock_attendance_repo: MagicMock,
    mock_membership_service: MagicMock,
):
    # Arrange
    me = make_user(user_id=5)
    obj = MagicMock()
    mock_attendance_repo.get_in_club.return_value = obj

    # Act
    result = attendance_service.get(club_id=1, attendance_id=123, me_id=me.id)
