from fastapi import APIRouter, status, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session as SASession

from ClubConnect.app.auth.deps import get_current_user
from ClubConnect.app.auth.membership_asserts import assert_is_member_of_club
from ClubConnect.app.crud.exercise import ExerciseNotFoundError, PlanNotFoundError, ConflictError
from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import Exercise
from ClubConnect.app.schemas.session import SessionCreate


exercises_router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/exercises",
    tags=["exercises"],
)


_ERROR_MAP = {
    ExerciseNotFoundError: (status.HTTP_404_NOT_FOUND, "Exercise not found"),
    PlanNotFoundError: (status.HTTP_404_NOT_FOUND, "Plan not found"),
    ConflictError: (status.HTTP_409_CONFLICT, "Position already taken"),
}
DOMAIN_ERRORS = tuple(_ERROR_MAP)

def to_http_exc(err: Exception) -> HTTPException:
    code, detail = _ERROR_MAP[err.__class__]
    return HTTPException(status_code=code, detail=detail)



@exercises_router.post("", response_model=Exercise, status_code=status.HTTP_201_CREATED)
def create_exercise_in_plan(
    club_id: int,
    plan_id: int,
    data: SessionCreate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return  create_exercise_in_plan(club_id, plan_id, data, db, me)
    except Exception as e:
        raise e

@exercises_router.get("", response_model=Exercise, status_code=status.HTTP_200_OK)
def list_exercises_in_plan(
    club_id: int,
    plan_id: int,
    data: SessionCreate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return list_exercises_in_plan(club_id, plan_id, data, db, me)
    except Exception as e:
        raise e


