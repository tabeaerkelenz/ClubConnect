from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

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

from app.exceptions.base import WorkoutNotFoundError, ConflictError, CoachOrOwnerRequiredError


router = APIRouter(tags=["WorkoutPlans"])


def _map_domain_error(e: Exception) -> HTTPException:
    if isinstance(e, WorkoutNotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if isinstance(e, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if isinstance(e, CoachOrOwnerRequiredError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


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
    try:
        return service.list_plans(club_id=club_id, user_id=user.id)
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.create_plan(club_id=club_id, user_id=user.id, data=payload.model_dump())
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.get_plan(club_id=club_id, plan_id=plan_id, user_id=user.id, nested=True)
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.update_plan(club_id=club_id, plan_id=plan_id, user_id=user.id, patch=patch)
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        service.delete_plan(club_id=club_id, plan_id=plan_id, user_id=user.id)
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.list_items(club_id=club_id, plan_id=plan_id, user_id=user.id)
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.create_item(
            club_id=club_id,
            plan_id=plan_id,
            user_id=user.id,
            data=payload.model_dump(),
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.update_item(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
            patch=patch,
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        service.delete_item(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.list_exercises(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.create_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            user_id=user.id,
            data=payload.model_dump(),
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        return service.update_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
            user_id=user.id,
            patch=patch,
        )
    except Exception as e:
        raise _map_domain_error(e)


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
    try:
        service.delete_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
            user_id=user.id,
        )
    except Exception as e:
        raise _map_domain_error(e)
