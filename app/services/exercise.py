from sqlalchemy.orm import Session as SASession
from app.crud.exercise import (
    create_exercise,
    list_exercises,
    get_exercise,
    update_exercise,
    delete_exercise,
    ExerciseNotFoundError,
    PlanNotFoundError,
    ConflictError,
)
from app.db.models import User
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate


def create_exercise_service(
    db: SASession, club_id: int, plan_id: int, me: User, data: ExerciseCreate
):
    try:
        return create_exercise(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
    except (PlanNotFoundError, ConflictError) as e:
        raise


def list_exercises_service(db: SASession, club_id: int, plan_id: int):
    try:
        return list_exercises(db, club_id=club_id, plan_id=plan_id)
    except PlanNotFoundError:
        raise


def get_exercise_service(
    db: SASession, club_id: int, plan_id: int, exercise_id: int, me: User
):
    try:
        return get_exercise(
            db, club_id=club_id, plan_id=plan_id, exercise_id=exercise_id, me=me
        )
    except (PlanNotFoundError, ExerciseNotFoundError) as e:
        raise


def update_exercise_service(
    db: SASession,
    club_id: int,
    plan_id: int,
    exercise_id: int,
    me: User,
    data: ExerciseUpdate,
):
    try:
        return update_exercise(
            db,
            club_id=club_id,
            plan_id=plan_id,
            exercise_id=exercise_id,
            me=me,
            data=data,
        )
    except (PlanNotFoundError, ExerciseNotFoundError, ConflictError) as e:
        raise


def delete_exercise_service(
    db: SASession, club_id: int, plan_id: int, exercise_id: int
):
    try:
        return delete_exercise(
            db, club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )
    except (PlanNotFoundError, ExerciseNotFoundError, ConflictError) as e:
        raise
