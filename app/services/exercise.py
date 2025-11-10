from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession, Session
from app.crud.exercise import (list_exercises, delete_exercise, get_plan_in_club, insert_exercise, next_position,
                               get_exercise_in_plan_and_club, update_exercise_fields, )
from app.db.models import User
from app.exceptions.base import PlanNotFoundError, PositionConflictError, ExerciseNotFoundError


def _is_unique_violation(e: IntegrityError) -> bool:
    return getattr(getattr(e, "orig", None), "pgcode", None) == "23505"


def create_exercise_service(db: Session, *, club_id: int, plan_id: int, data, me):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()

    payload = data.model_dump(exclude_none=True)
    desired_pos = payload.get("position")

    try:
        for _ in range(3):
            pos = desired_pos if desired_pos is not None else next_position(db, plan_id)
            try:
                obj = insert_exercise(
                    db, plan_id=plan_id,
                    name=data.name,
                    description=data.description,
                    sets=data.sets,
                    repetitions=data.repetitions,
                    position=pos,
                    day_label=data.day_label,
                )
                db.commit()
                db.refresh(obj)
                return obj
            except IntegrityError as e:
                db.rollback()
                if desired_pos is None and _is_unique_violation(e):
                    # race on auto-append → try next position
                    continue
                # explicit position or other constraint → conflict
                raise PositionConflictError() from e
        # exhausted retries
        raise PositionConflictError()
    except Exception:
        db.rollback()
        raise


def list_exercises_service(db: SASession, club_id: int, plan_id: int):
    try:
        return list_exercises(db, club_id=club_id, plan_id=plan_id)
    except Exception as e:
        raise ExerciseNotFoundError() from e


def get_exercise_service(
    db: SASession, club_id: int, plan_id: int, exercise_id: int, me: User
):
    try:
        return get_exercise_in_plan_and_club(
            db, club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )
    except Exception as e:
        raise ExerciseNotFoundError() from e


def update_exercise_service(db: Session, *, club_id: int, plan_id: int, exercise_id: int, data, me):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()
    exercise = get_exercise_in_plan_and_club(db, club_id, plan_id, exercise_id)
    if not exercise:
        raise ExerciseNotFoundError()

    updates = data.model_dump(exclude_unset=True)
    if "position" in updates and updates["position"] is None:
        updates.pop("position")

    try:
        update_exercise_fields(db, exercise, **updates)
        db.commit()
        db.refresh(exercise)
        return exercise
    except IntegrityError as e:
        db.rollback()
        if _is_unique_violation(e) and "position" in updates:
            raise PositionConflictError() from e
        raise



def delete_exercise_service(db: Session, *, club_id: int, plan_id: int, exercise_id: int):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()
    obj = get_exercise_in_plan_and_club(db, club_id, plan_id, exercise_id)
    if not obj:
        raise ExerciseNotFoundError()

    try:
        delete_exercise(db, obj)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # for later if i add “can’t delete if referenced” → raise a domain error here
        raise
