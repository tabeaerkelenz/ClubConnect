from fastapi import APIRouter, Depends, status
from typing import List

from app.auth.deps import get_current_user
from app.schemas.exercise import ExerciseRead, ExerciseCreate, ExerciseUpdate
from app.services.exercise import ExerciseService
from app.core.dependencies import get_exercise_service

exercises_router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/exercises",
    tags=["exercises"],
)


@exercises_router.get("", response_model=List[ExerciseRead])
def list_exercises_in_plan(
    club_id: int,
    plan_id: int,
    service: ExerciseService = Depends(get_exercise_service),
    me=Depends(get_current_user),
):
    return service.list_exercises(club_id=club_id, plan_id=plan_id, user_id=me.id)


@exercises_router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise_in_plan(
    club_id: int,
    plan_id: int,
    data: ExerciseCreate,
    service: ExerciseService = Depends(get_exercise_service),
    me=Depends(get_current_user),
):
    return service.create_exercise(
        club_id=club_id, plan_id=plan_id, user_id=me.id, data=data
    )


@exercises_router.get("/{exercise_id}", response_model=ExerciseRead)
def get_exercise_in_plan(
    club_id: int,
    plan_id: int,
    exercise_id: int,
    service: ExerciseService = Depends(get_exercise_service),
    me=Depends(get_current_user),
):
    return service.get_exercise(
        club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, user_id=me.id
    )


@exercises_router.patch("/{exercise_id}", response_model=ExerciseRead)
def update_exercise_in_plan(
    club_id: int,
    plan_id: int,
    exercise_id: int,
    data: ExerciseUpdate,
    service: ExerciseService = Depends(get_exercise_service),
    me=Depends(get_current_user),
):
    return service.update_exercise(
        club_id=club_id,
        plan_id=plan_id,
        exercise_id=exercise_id,
        user_id=me.id,
        data=data,
    )


@exercises_router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise_in_plan(
    club_id: int,
    plan_id: int,
    exercise_id: int,
    service: ExerciseService = Depends(get_exercise_service),
    me=Depends(get_current_user),
):
    service.delete_exercise(
        club_id=club_id,
        plan_id=plan_id,
        exercise_id=exercise_id,
        user_id=me.id,
    )
