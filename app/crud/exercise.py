import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession

from app.db.models import Plan, Exercise


class ExerciseNotFoundError(Exception):
    """Exercise not found."""
    pass
class PlanNotFoundError(Exception):
    """Plan not found."""
    pass
class ConflictError(Exception):
    """Position already taken."""
    pass

def _get_plan_in_club_or_raise(db: SASession, club_id: int, plan_id: int) -> Plan:
    stmt = sa.select(Plan).where(Plan.id == plan_id, Plan.club_id == club_id,)
    plan = db.execute(stmt).scalar_one_or_none()
    if not plan:
        raise PlanNotFoundError()
    return plan

def _get_exercise_in_plan_and_club_or_raise(
    db: SASession, club_id: int, plan_id: int, exercise_id: int
) -> Exercise:
    stmt = (
        sa.select(Exercise)
        .join(Plan, Plan.id == Exercise.plan_id)
        .where(
            Exercise.id == exercise_id,
            Exercise.plan_id == plan_id,
            Plan.club_id == club_id,
        )
    )
    exercise = db.execute(stmt).scalar_one_or_none()
    if not exercise:
        # If you have ExerciseNotFound, raise that; else reuse PlanNotFoundError
        raise PlanNotFoundError()
    return exercise


def _next_position(db: SASession, plan_id: int) -> int:
    stmt = sa.select(sa.func.coalesce(sa.func.max(Exercise.position) + 1, 0)).where(Exercise.plan_id == plan_id)
    return db.execute(stmt).scalar_one()

def create_exercise(db: SASession, club_id: int, plan_id: int, me, data) -> Exercise:
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    payload = data.model_dump(exclude_none=True)
    desired_pos = payload.get("position")

    for _ in range(3):
        pos = desired_pos if desired_pos is not None else _next_position(db, plan_id)

        obj = Exercise(
            plan_id=plan_id,
            name=data.name,  # required
            description=data.description,  # optional -> may be None
            sets=data.sets,
            repetitions=data.repetitions,
            position=pos,
            day_label=data.day_label,
        )

        db.add(obj)
        try:
            db.commit()
            db.refresh(obj)
            return obj
        except IntegrityError as e:
            db.rollback()
            # Unique collision on (plan_id, position): recompute and retry only if auto-append
            # PostgreSQL code for unique violation is 23505
            pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
            if desired_pos is None and pgcode == "23505":
                # another insert took this position; loop and try next _next_position()
                continue
            raise ConflictError()

    raise ConflictError()


def list_exercises(db: SASession, club_id: int, plan_id: int) -> list[Exercise]:
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    stmt = sa.select(Exercise).where(Exercise.plan_id == plan_id).order_by(Exercise.position.asc())
    exercises = db.execute(stmt).scalars().all()

    return exercises

def get_exercise(db: SASession, club_id: int, plan_id: int, exercise_id: int, me) -> Exercise:
    return _get_exercise_in_plan_and_club_or_raise(db, club_id, plan_id, exercise_id)


def update_exercise(db: SASession, club_id: int, plan_id: int, exercise_id: int, me, data) -> Exercise:
    exercise = _get_exercise_in_plan_and_club_or_raise(db, club_id, plan_id, exercise_id)

    updates = data.model_dump(exclude_unset=True)
    # If position omitted → no change; if provided and None → drop it
    if "position" in updates and updates["position"] is None:
        updates.pop("position")

    for k, v in updates.items():
        setattr(exercise, k, v)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # if position changed and collided → Conflict
        pgcode = getattr(getattr(e, "orig", None), "pgcode", None)
        if ("position" in updates) and pgcode == "23505":
            raise ConflictError()
        raise ConflictError()
    db.refresh(exercise)
    return exercise


def delete_exercise(db: SASession, club_id: int, plan_id: int, exercise_id: int) -> Exercise:
    exercise = _get_exercise_in_plan_and_club_or_raise(db, club_id, plan_id, exercise_id)
    db.delete(exercise)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        ConflictError()
    return None




