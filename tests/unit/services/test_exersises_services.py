import pytest
from unittest.mock import MagicMock

from app.services.exercise import ExerciseService
from app.repositories.exercise import ExerciseRepository
from app.services.membership import MembershipService
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate
from app.exceptions.base import (
    NotClubMember,
    CoachOrOwnerRequiredError,
    PlanNotFoundError,
    ExerciseNotFoundError,
    PositionConflictError,
)

from factories import make_user


# ---------- fixtures ----------

@pytest.fixture
def mock_exercise_repo() -> MagicMock:
    return MagicMock(spec=ExerciseRepository)


@pytest.fixture
def mock_membership_service() -> MagicMock:
    return MagicMock(spec=MembershipService)


@pytest.fixture
def exercise_service(
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
) -> ExerciseService:
    return ExerciseService(
        exercise_repo=mock_exercise_repo,
        membership_service=mock_membership_service,
    )


@pytest.fixture
def user():
    return make_user(user_id=42)


# ---------- happy paths ----------

def test_list_exercises_happy_path(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    expected = [MagicMock(), MagicMock()]
    mock_exercise_repo.list_in_plan.return_value = expected

    result = exercise_service.list_exercises(
        club_id=club_id, plan_id=plan_id, user_id=user.id
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_exercise_repo.list_in_plan.assert_called_once_with(
        club_id=club_id, plan_id=plan_id
    )
    assert result == expected


def test_get_exercise_happy_path(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    exercise_id = 99
    expected = MagicMock()
    mock_exercise_repo.get_in_plan.return_value = expected

    result = exercise_service.get_exercise(
        club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, user_id=user.id
    )

    mock_membership_service.require_member_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_exercise_repo.get_in_plan.assert_called_once_with(
        club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
    )
    assert result == expected


def test_create_exercise_happy_path(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10

    data = MagicMock(spec=ExerciseCreate)
    data.name = "Squats"
    data.description = None
    data.sets = 3
    data.repetitions = 10
    data.position = None
    data.day_label = None

    created = MagicMock()
    mock_exercise_repo.create_in_plan.return_value = created

    result = exercise_service.create_exercise(
        club_id=club_id, plan_id=plan_id, user_id=user.id, data=data
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_exercise_repo.create_in_plan.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
        name=data.name,
        description=data.description,
        sets=data.sets,
        repetitions=data.repetitions,
        position=data.position,
        day_label=data.day_label,
    )
    assert result == created


def test_update_exercise_happy_path(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    exercise_id = 99

    data = MagicMock(spec=ExerciseUpdate)
    data.model_dump.return_value = {"name": "New Name", "position": 2}

    updated = MagicMock()
    mock_exercise_repo.update_in_plan.return_value = updated

    result = exercise_service.update_exercise(
        club_id=club_id,
        plan_id=plan_id,
        exercise_id=exercise_id,
        user_id=user.id,
        data=data,
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_exercise_repo.update_in_plan.assert_called_once_with(
        club_id=club_id,
        plan_id=plan_id,
        exercise_id=exercise_id,
        updates={"name": "New Name", "position": 2},
    )
    assert result == updated


def test_delete_exercise_happy_path(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    exercise_id = 99

    result = exercise_service.delete_exercise(
        club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, user_id=user.id
    )

    mock_membership_service.require_coach_or_owner_of_club.assert_called_once_with(
        club_id=club_id, user_id=user.id
    )
    mock_exercise_repo.delete_in_plan.assert_called_once_with(
        club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
    )
    assert result is None


# ---------- guard failure stops repo ----------

def test_list_exercises_guard_failure_stops_repo(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10

    mock_membership_service.require_member_of_club.side_effect = NotClubMember()

    with pytest.raises(NotClubMember):
        exercise_service.list_exercises(club_id=club_id, plan_id=plan_id, user_id=user.id)

    mock_exercise_repo.list_in_plan.assert_not_called()


def test_create_exercise_guard_failure_stops_repo(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    mock_membership_service: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10

    mock_membership_service.require_coach_or_owner_of_club.side_effect = CoachOrOwnerRequiredError()

    data = MagicMock(spec=ExerciseCreate)

    with pytest.raises(CoachOrOwnerRequiredError):
        exercise_service.create_exercise(club_id=club_id, plan_id=plan_id, user_id=user.id, data=data)

    mock_exercise_repo.create_in_plan.assert_not_called()


# ---------- repo error propagation ----------

def test_list_exercises_propagates_plan_not_found(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    user,
):
    club_id = 1
    plan_id = 999

    mock_exercise_repo.list_in_plan.side_effect = PlanNotFoundError()

    with pytest.raises(PlanNotFoundError):
        exercise_service.list_exercises(club_id=club_id, plan_id=plan_id, user_id=user.id)


def test_get_exercise_propagates_not_found(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    exercise_id = 999

    mock_exercise_repo.get_in_plan.side_effect = ExerciseNotFoundError()

    with pytest.raises(ExerciseNotFoundError):
        exercise_service.get_exercise(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, user_id=user.id
        )


def test_update_exercise_propagates_position_conflict(
    exercise_service: ExerciseService,
    mock_exercise_repo: MagicMock,
    user,
):
    club_id = 1
    plan_id = 10
    exercise_id = 99

    data = MagicMock(spec=ExerciseUpdate)
    data.model_dump.return_value = {"position": 1}

    mock_exercise_repo.update_in_plan.side_effect = PositionConflictError()

    with pytest.raises(PositionConflictError):
        exercise_service.update_exercise(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, user_id=user.id, data=data
        )
