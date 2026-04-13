from unittest.mock import MagicMock, patch

import pytest

from app.services.workout_plan_ai import WorkoutPlanAIService, FEATURE_WORKOUTPLAN_DRAFT
from app.services.workout_plan import WorkoutPlanService
from app.repositories.ai_usage import AIUsageRepository
from app.repositories.club import ClubRepository
from app.schemas.workout_plan_ai import WorkoutPlanAIDraftRequest, WorkoutPlanAIDraft, AIDraftItem, AIDraftExercise
from app.exceptions.base import RateLimitError
from .factories import make_club


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_workout_plan_service() -> MagicMock:
    return MagicMock(spec=WorkoutPlanService)


@pytest.fixture
def mock_ai_usage_repo() -> MagicMock:
    return MagicMock(spec=AIUsageRepository)


@pytest.fixture
def mock_club_repo() -> MagicMock:
    return MagicMock(spec=ClubRepository)


@pytest.fixture
def ai_svc(mock_workout_plan_service, mock_ai_usage_repo, mock_club_repo):
    with patch("app.services.workout_plan_ai.OpenAI"):
        svc = WorkoutPlanAIService(
            workout_plan_service=mock_workout_plan_service,
            ai_usage_repo=mock_ai_usage_repo,
            club_repo=mock_club_repo,
            daily_limit=3,
        )
    svc.client = MagicMock()
    return svc


def make_draft_request(**overrides) -> WorkoutPlanAIDraftRequest:
    return WorkoutPlanAIDraftRequest(
        goal="Build strength",
        level="beginner",
        duration_weeks=4,
        days_per_week=3,
        **overrides,
    )


def make_draft_json(name: str = "4-Week Plan") -> str:
    draft = WorkoutPlanAIDraft(
        name=name,
        description="A solid plan",
        goal="Build strength",
        level="beginner",
        duration_weeks=4,
        items=[
            AIDraftItem(
                week_number=1,
                order_index=0,
                title="Day 1",
                exercises=[
                    AIDraftExercise(name="Squat", sets=3, repetitions=10, position=0),
                ],
            )
        ],
    )
    return draft.model_dump_json()


# ---------------------------------------------------------------------------
# Quota check
# ---------------------------------------------------------------------------

def test_raises_rate_limit_when_quota_exceeded(ai_svc, mock_ai_usage_repo):
    mock_ai_usage_repo.count_today.return_value = 3  # at the limit

    with pytest.raises(RateLimitError):
        ai_svc.generate_and_create_plan(
            club_id=10, user_id=42, req=make_draft_request()
        )

    mock_ai_usage_repo.count_today.assert_called_once_with(
        user_id=42, feature=FEATURE_WORKOUTPLAN_DRAFT
    )
    ai_svc.client.responses.create.assert_not_called()


def test_quota_check_uses_correct_feature_key(ai_svc, mock_ai_usage_repo):
    mock_ai_usage_repo.count_today.return_value = 99

    with pytest.raises(RateLimitError):
        ai_svc.generate_and_create_plan(club_id=10, user_id=1, req=make_draft_request())

    _, kwargs = mock_ai_usage_repo.count_today.call_args
    assert kwargs["feature"] == FEATURE_WORKOUTPLAN_DRAFT


# ---------------------------------------------------------------------------
# Happy path — plan creation
# ---------------------------------------------------------------------------

def test_creates_plan_and_items_and_exercises(
    ai_svc, mock_ai_usage_repo, mock_club_repo, mock_workout_plan_service
):
    mock_ai_usage_repo.count_today.return_value = 0
    mock_club_repo.get_club.return_value = make_club(club_id=10, name="FC Test")
    ai_svc.client.responses.create.return_value.output_text = make_draft_json()

    created_plan = MagicMock()
    created_plan.id = 1
    created_item = MagicMock()
    created_item.id = 5
    mock_workout_plan_service.create_plan.return_value = created_plan
    mock_workout_plan_service.create_item.return_value = created_item

    ai_svc.generate_and_create_plan(club_id=10, user_id=42, req=make_draft_request())

    mock_workout_plan_service.create_plan.assert_called_once()
    mock_workout_plan_service.create_item.assert_called_once()
    mock_workout_plan_service.create_exercise.assert_called_once()


def test_records_usage_after_successful_generation(
    ai_svc, mock_ai_usage_repo, mock_club_repo, mock_workout_plan_service
):
    mock_ai_usage_repo.count_today.return_value = 0
    mock_club_repo.get_club.return_value = make_club(club_id=10, name="FC Test")
    ai_svc.client.responses.create.return_value.output_text = make_draft_json()

    created_plan = MagicMock()
    created_plan.id = 1
    mock_workout_plan_service.create_plan.return_value = created_plan
    mock_workout_plan_service.create_item.return_value = MagicMock(id=5)

    ai_svc.generate_and_create_plan(club_id=10, user_id=42, req=make_draft_request())

    mock_ai_usage_repo.record.assert_called_once_with(
        user_id=42, club_id=10, feature=FEATURE_WORKOUTPLAN_DRAFT
    )


def test_does_not_record_usage_if_openai_fails(
    ai_svc, mock_ai_usage_repo, mock_club_repo
):
    mock_ai_usage_repo.count_today.return_value = 0
    mock_club_repo.get_club.return_value = make_club(club_id=10, name="FC Test")
    ai_svc.client.responses.create.side_effect = Exception("OpenAI unavailable")

    with pytest.raises(Exception, match="OpenAI unavailable"):
        ai_svc.generate_and_create_plan(club_id=10, user_id=42, req=make_draft_request())

    mock_ai_usage_repo.record.assert_not_called()


def test_returns_nested_plan(
    ai_svc, mock_ai_usage_repo, mock_club_repo, mock_workout_plan_service
):
    mock_ai_usage_repo.count_today.return_value = 0
    mock_club_repo.get_club.return_value = make_club(club_id=10, name="FC Test")
    ai_svc.client.responses.create.return_value.output_text = make_draft_json()

    created_plan = MagicMock()
    created_plan.id = 1
    nested_plan = MagicMock()
    mock_workout_plan_service.create_plan.return_value = created_plan
    mock_workout_plan_service.create_item.return_value = MagicMock(id=5)
    mock_workout_plan_service.get_plan.return_value = nested_plan

    result = ai_svc.generate_and_create_plan(club_id=10, user_id=42, req=make_draft_request())

    mock_workout_plan_service.get_plan.assert_called_once_with(
        club_id=10, plan_id=1, user_id=42, nested=True
    )
    assert result is nested_plan
