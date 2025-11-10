import sqlalchemy as sa
from sqlalchemy.orm import Session as SASession, Session

from app.db.models import Plan, Exercise

def get_plan_in_club(db: Session, club_id: int, plan_id: int) -> Plan | None:
    stmt = sa.select(Plan).where(Plan.id == plan_id, Plan.club_id == club_id)
    return db.execute(stmt).scalar_one_or_none()


def get_exercise_in_plan_and_club(
    db: SASession, club_id: int, plan_id: int, exercise_id: int
) -> Exercise:
    """Get exercise by id, plan_id and club_id or raise ExerciseNotFoundError."""
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
    return exercise


def next_position(db: SASession, plan_id: int) -> int:
    """Get the next available position for an exercise in a plan."""
    stmt = sa.select(sa.func.coalesce(sa.func.max(Exercise.position) + 1, 0)).where(
        Exercise.plan_id == plan_id
    )
    return db.execute(stmt).scalar_one()


def insert_exercise(db: Session, *, plan_id: int, **fields) -> Exercise:
    exercise = Exercise(plan_id=plan_id, **fields)
    db.add(exercise)
    db.flush()
    return exercise


def list_exercises(db: SASession, club_id: int, plan_id: int) -> list[Exercise]:
    """List all exercises in a plan within a club, ordered by position ascending."""
    stmt = (
        sa.select(Exercise)
        .where(Exercise.plan_id == plan_id)
        .order_by(Exercise.position.asc())
    )
    exercises = db.execute(stmt).scalars().all()

    return exercises


def update_exercise_fields(db: Session, exercise: Exercise, **updates) -> Exercise:
    for k, v in updates.items():
        setattr(exercise, k, v)
    db.flush()
    return exercise


def delete_exercise(db: Session, exercise: Exercise) -> None:
    db.delete(exercise)
    db.flush()
