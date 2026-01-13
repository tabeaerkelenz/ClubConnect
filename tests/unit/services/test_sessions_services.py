import pytest
from unittest.mock import MagicMock

from app.services.session import SessionService
from app.repositories.session import SessionRepository
from app.services.membership import MembershipService
from app.schemas.session import SessionCreate, SessionUpdate
from app.exceptions.base import InvalidTimeRange

from .factories import make_user


# ---------- fixtures ----------

@pytest.fixture
def mock_session_repo() -> MagicMock:
    return MagicMock(spec=SessionRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def session_service(
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
) -> SessionService:
    return SessionService(
        session_repo=mock_session_repo,
        membership_service=mock_membership_service,
    )


@pytest.fixture
def user():
    return make_user(user_id=42)


# ---------- tests ----------

def test_list_sessions_requires_member_guard(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    expected = []

    mock_session_repo.list_in_plan.return_value = expected

    result = session_service.list_sessions(
        club_id=club_id, plan_id=plan_id, user_id=user.id
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_session_repo.list_in_plan.assert_called_once_with(
        club_id=club_id, plan_id=plan_id
    )
    assert result == expected


def test_get_session_requires_member_guard(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    session_id = 123
    expected_session = MagicMock()

    mock_session_repo.get_in_plan.return_value = expected_session

    result = session_service.get_session(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        user_id=user.id,
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_session_repo.get_in_plan.assert_called_once_with(
        club_id=club_id, plan_id=plan_id, session_id=session_id
    )
    assert result == expected_session


def test_create_session_requires_coach_or_owner(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10

    data = MagicMock(spec=SessionCreate)
    data.name = "Leg day"
    data.description = None
    data.starts_at = MagicMock()
    data.ends_at = MagicMock()
    data.location = "Gym"
    data.note = None

    created = MagicMock()
    mock_session_repo.create_in_plan.return_value = created

    result = session_service.create_session(
        club_id=club_id,
        plan_id=plan_id,
        user_id=user.id,
        data=data,
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_session_repo.create_in_plan.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
        created_by_id=user.id,
        name=data.name,
        description=data.description,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        location=data.location,
        note=data.note,
    )
    assert result == created


def test_update_session_updates_fields_when_no_time_change(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    session_id = 123

    data = MagicMock(spec=SessionUpdate)
    data.model_dump.return_value = {"location": "New Gym"}

    updated = MagicMock()
    mock_session_repo.update_in_plan.return_value = updated

    result = session_service.update_session(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        user_id=user.id,
        data=data,
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_session_repo.get_in_plan.assert_not_called()
    mock_session_repo.update_in_plan.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        updates={"location": "New Gym"},
    )
    assert result == updated


def test_update_session_validates_time_range(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    session_id = 123

    class FakeTime:
        def __init__(self, v): self.v = v
        def __ge__(self, other): return self.v >= other.v

    data = MagicMock(spec=SessionUpdate)
    data.model_dump.return_value = {
        "starts_at": FakeTime(10),
        "ends_at": FakeTime(5),
    }

    existing = MagicMock()
    existing.starts_at = FakeTime(1)
    existing.ends_at = FakeTime(2)

    mock_session_repo.get_in_plan.return_value = existing

    with pytest.raises(InvalidTimeRange):
        session_service.update_session(
            club_id=club_id,
            plan_id=plan_id,
            session_id=session_id,
            user_id=user.id,
            data=data,
        )

    mock_session_repo.update_in_plan.assert_not_called()


def test_delete_session_requires_coach_or_owner(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    session_id = 123

    session_service.delete_session(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        user_id=user.id,
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_session_repo.delete_in_plan.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
    )


def test_delete_session_no_return_value(
    session_service: SessionService,
    mock_session_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    session_id = 123

    result = session_service.delete_session(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        user_id=user.id,
    )

    assert result is None