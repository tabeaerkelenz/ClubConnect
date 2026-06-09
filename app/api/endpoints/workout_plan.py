from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.schemas.workout_plan import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    WorkoutPlanRead,
    WorkoutPlanReadNested,
    WorkoutPlanItemCreate,
    WorkoutPlanItemUpdate,
    WorkoutPlanItemRead,
    WorkoutPlanExerciseCreate,
    WorkoutPlanExerciseUpdate,
    WorkoutPlanExerciseRead,
)

from app.services.workout_plan import WorkoutPlanService

from app.core.dependencies import get_workout_plan_service
from app.auth.deps import get_current_user
from app.models.models import User



router = APIRouter(tags=["WorkoutPlans"])

# -------------------------
# Plans
# -------------------------

@router.get(
    "/clubs/{club_id}/workout-plans",
    response_model=list[WorkoutPlanRead],
)
def list_workout_plans(
    club_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.list_plans(club_id=club_id, user_id=user.id)



@router.post(
    "/clubs/{club_id}/workout-plans",
    response_model=WorkoutPlanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workout_plan(
    club_id: int,
    payload: WorkoutPlanCreate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.create_plan(club_id=club_id, user_id=user.id, data=payload.model_dump())



@router.get(
    "/clubs/{club_id}/workout-plans/{plan_id}",
    response_model=WorkoutPlanReadNested,
)
def get_workout_plan_nested(
    club_id: int,
    plan_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.get_plan(club_id=club_id, plan_id=plan_id, user_id=user.id, nested=True)


@router.patch(
    "/clubs/{club_id}/workout-plans/{plan_id}",
    response_model=WorkoutPlanRead,
)
def update_workout_plan(
    club_id: int,
    plan_id: int,
    payload: WorkoutPlanUpdate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    return service.update_plan(club_id=club_id, plan_id=plan_id, user_id=user.id, patch=patch)



@router.delete(
    "/clubs/{club_id}/workout-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_workout_plan(
    club_id: int,
    plan_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    service.delete_plan(club_id=club_id, plan_id=plan_id, user_id=user.id)



# -------------------------
# Items
# -------------------------

@router.get(
    "/clubs/{club_id}/workout-plans/{plan_id}/items",
    response_model=list[WorkoutPlanItemRead],
)
def list_items(
    club_id: int,
    plan_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.list_items(club_id=club_id, plan_id=plan_id, user_id=user.id)



@router.post(
    "/clubs/{club_id}/workout-plans/{plan_id}/items",
    response_model=WorkoutPlanItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_item(
    club_id: int,
    plan_id: int,
    payload: WorkoutPlanItemCreate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.create_item(
            club_id=club_id,
            plan_id=plan_id,
            user_id=user.id,
            data=payload.model_dump(),
        )



@router.patch(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}",
    response_model=WorkoutPlanItemRead,
)
def update_item(
    club_id: int,
    plan_id: int,
    item_id: int,
    payload: WorkoutPlanItemUpdate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    return service.update_item(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
            patch=patch,
        )


@router.delete(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_item(
    club_id: int,
    plan_id: int,
    item_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    service.delete_item(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
        )


# -------------------------
# Exercises
# -------------------------

@router.get(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}/exercises",
    response_model=list[WorkoutPlanExerciseRead],
)
def list_exercises(
    club_id: int,
    plan_id: int,
    item_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.list_exercises(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
        )


@router.post(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}/exercises",
    response_model=WorkoutPlanExerciseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_exercise(
    club_id: int,
    plan_id: int,
    item_id: int,
    payload: WorkoutPlanExerciseCreate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    return service.create_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
            data=payload.model_dump(),
        )


@router.patch(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}/exercises/{exercise_id}",
    response_model=WorkoutPlanExerciseRead,
)
def update_exercise(
    club_id: int,
    plan_id: int,
    item_id: int,
    exercise_id: int,
    payload: WorkoutPlanExerciseUpdate,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    patch = payload.model_dump(exclude_unset=True)
    return service.update_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
            user_id=user.id,
            patch=patch,
        )


@router.delete(
    "/clubs/{club_id}/workout-plans/{plan_id}/items/{item_id}/exercises/{exercise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_exercise(
    club_id: int,
    plan_id: int,
    item_id: int,
    exercise_id: int,
    service: WorkoutPlanService = Depends(get_workout_plan_service),
    user: User = Depends(get_current_user),
):
    service.delete_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
            user_id=user.id,
        )
