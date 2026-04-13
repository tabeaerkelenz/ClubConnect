from fastapi import APIRouter, Depends, status

from app.schemas.workout_plan import WorkoutPlanReadNested
from app.schemas.workout_plan_ai import WorkoutPlanAIDraftRequest
from app.services.workout_plan_ai import WorkoutPlanAIService

from app.core.dependencies import get_workout_plan_ai_service
from app.auth.deps import get_current_user
from app.models.models import User


router = APIRouter(tags=["WorkoutPlans-AI"])


@router.post(
    "/clubs/{club_id}/workout-plans/ai-draft",
    response_model=WorkoutPlanReadNested,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_plan_ai_draft(
    club_id: int,
    payload: WorkoutPlanAIDraftRequest,
    ai_service: WorkoutPlanAIService = Depends(get_workout_plan_ai_service),
    user: User = Depends(get_current_user),
):
    return ai_service.generate_and_create_plan(
        club_id=club_id,
        user_id=user.id,
        req=payload,
    )
