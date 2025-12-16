from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Exercise, Plan
from app.models.models import DayLabel
from app.exceptions.base import (
    PlanNotFoundError,
    ExerciseNotFoundError,
    PositionConflictError,
    ConflictError,
)


def _is_unique_violation(e: IntegrityError) -> bool:
    # Postgres unique violation
    return getattr(getattr(e, "orig", None), "pgcode", None) == "23505"


class ExerciseRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- helpers ----------

    def _get_plan_in_club(self, *, club_id: int, plan_id: int) -> Plan:
        stmt = sa.select(Plan).where(
            Plan.id == plan_id,
            Plan.club_id == club_id,
        )
        plan = self.db.execute(stmt).scalar_one_or_none()
        if not plan:
            raise PlanNotFoundError()
        return plan

    def _get_exercise_in_plan(
        self, *, club_id: int, plan_id: int, exercise_id: int
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
        exercise = self.db.execute(stmt).scalar_one_or_none()
        if not exercise:
            raise ExerciseNotFoundError()
        return exercise

    def _next_position(self, *, plan_id: int) -> int:
        # returns 0 if no exercises yet
        stmt = sa.select(sa.func.coalesce(sa.func.max(Exercise.position) + 1, 0)).where(
            Exercise.plan_id == plan_id
        )
        return self.db.execute(stmt).scalar_one()

    # ---------- public API ----------

    def list_in_plan(self, *, club_id: int, plan_id: int) -> list[Exercise]:
        # strict: plan must exist in club
        self._get_plan_in_club(club_id=club_id, plan_id=plan_id)

        stmt = (
            sa.select(Exercise)
            .where(Exercise.plan_id == plan_id)
            .order_by(Exercise.position.asc(), Exercise.id.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_in_plan(
        self, *, club_id: int, plan_id: int, exercise_id: int
    ) -> Exercise:
        return self._get_exercise_in_plan(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )

    def create_in_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        name: str,
        description: str | None,
        sets: int | None,
        repetitions: int | None,
        position: int | None,
        day_label: DayLabel | None,
        _retries: int = 3,
    ) -> Exercise:
        self._get_plan_in_club(club_id=club_id, plan_id=plan_id)

        payload = dict(
            plan_id=plan_id,
            name=name,
            description=description,
            sets=sets,
            repetitions=repetitions,
            day_label=day_label,
        )

        desired_pos = position

        # auto-append: retry on unique violation (race)
        if desired_pos is None:
            last_err: IntegrityError | None = None
            for _ in range(_retries):
                pos = self._next_position(plan_id=plan_id)
                exercise = Exercise(**payload, position=pos)

                try:
                    self.db.add(exercise)
                    self.db.commit()
                    self.db.refresh(exercise)
                    return exercise
                except IntegrityError as e:
                    self.db.rollback()
                    last_err = e
                    if _is_unique_violation(e):
                        # race on position -> try next
                        continue
                    raise ConflictError() from e

            # exhausted retries
            raise PositionConflictError() from last_err

        # explicit position: single attempt; unique violation => PositionConflictError
        exercise = Exercise(**payload, position=desired_pos)

        try:
            self.db.add(exercise)
            self.db.commit()
            self.db.refresh(exercise)
            return exercise
        except IntegrityError as e:
            self.db.rollback()
            if _is_unique_violation(e):
                raise PositionConflictError() from e
            raise ConflictError() from e

    def update_in_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        exercise_id: int,
        updates: dict,
    ) -> Exercise:
        exercise = self._get_exercise_in_plan(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )

        for key, value in updates.items():
            setattr(exercise, key, value)

        try:
            self.db.commit()
            self.db.refresh(exercise)
            return exercise
        except IntegrityError as e:
            self.db.rollback()
            if _is_unique_violation(e) and "position" in updates:
                raise PositionConflictError() from e
            raise ConflictError() from e

    def delete_in_plan(self, *, club_id: int, plan_id: int, exercise_id: int) -> None:
        exercise = self._get_exercise_in_plan(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )

        try:
            self.db.delete(exercise)
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError() from e
