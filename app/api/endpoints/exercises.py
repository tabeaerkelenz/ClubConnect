from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session as SASession

from app.auth.deps import get_current_user
from app.auth.membership_deps import assert_is_member_of_club
from app.db.deps import get_db
from app.services.exercise import *
from app.schemas.exercise import ExerciseRead, ExerciseCreate, ExerciseListParams

from app.services.exercise import create_exercise_service, list_exercises_service

exercises_router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/exercises",
    tags=["exercises"],
)


@exercises_router.post(
    "", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED
)
def create_exercise_in_plan(
    club_id: int,
    plan_id: int,
    data: ExerciseCreate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    return create_exercise_service(db, club_id, plan_id, me, data)


@exercises_router.get(
    "", response_model=list[ExerciseRead], status_code=status.HTTP_200_OK
)
def list_exercises_in_plan(
    club_id: int,
    plan_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    return list_exercises_service(db, club_id, plan_id)
