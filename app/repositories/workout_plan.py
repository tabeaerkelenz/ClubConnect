from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.models import WorkoutPlan, WorkoutPlanItem, WorkoutPlanExercise

from app.exceptions.base import WorkoutNotFoundError, ConflictError


class WorkoutPlanRepository:
    def __init__(self, db: Session):
        self.db = db

    # -------------------------
    # Plans
    # -------------------------

    def list_plans(self, club_id: int) -> Sequence[WorkoutPlan]:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.club_id == club_id)
            .order_by(WorkoutPlan.id.desc())
        )
        return self.db.execute(stmt).scalars().all()

    def create_plan(self, club_id: int, created_by_id: int, data: dict) -> WorkoutPlan:
        plan = WorkoutPlan(
            club_id=club_id,
            created_by_id=created_by_id,
            **data,
        )
        self.db.add(plan)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # e.g. uq_workout_plans_club_name
            raise ConflictError("WorkoutPlan conflict") from e
        self.db.refresh(plan)
        return plan

    def get_plan(self, club_id: int, plan_id: int) -> WorkoutPlan:
        stmt = select(WorkoutPlan).where(
            WorkoutPlan.club_id == club_id,
            WorkoutPlan.id == plan_id,
        )
        plan = self.db.execute(stmt).scalars().first()
        if not plan:
            raise WorkoutNotFoundError("WorkoutPlan not found")
        return plan

    def get_plan_nested(self, club_id: int, plan_id: int) -> WorkoutPlan:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.club_id == club_id, WorkoutPlan.id == plan_id)
            .options(
                selectinload(WorkoutPlan.items).selectinload(WorkoutPlanItem.exercises)
            )
        )
        plan = self.db.execute(stmt).scalars().first()
        if not plan:
            raise WorkoutNotFoundError("WorkoutPlan not found")
        return plan

    def update_plan(self, club_id: int, plan_id: int, patch: dict) -> WorkoutPlan:
        plan = self.get_plan(club_id=club_id, plan_id=plan_id)
        for k, v in patch.items():
            setattr(plan, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("WorkoutPlan conflict") from e
        self.db.refresh(plan)
        return plan

    def delete_plan(self, club_id: int, plan_id: int) -> None:
        plan = self.get_plan(club_id=club_id, plan_id=plan_id)
        self.db.delete(plan)
        self.db.commit()

    # -------------------------
    # Items (club-scoped via join to plan)
    # -------------------------

    def list_items(self, club_id: int, plan_id: int) -> Sequence[WorkoutPlanItem]:
        # ensures plan belongs to club
        self.get_plan(club_id=club_id, plan_id=plan_id)

        stmt = (
            select(WorkoutPlanItem)
            .where(WorkoutPlanItem.plan_id == plan_id)
            .order_by(WorkoutPlanItem.order_index.asc(), WorkoutPlanItem.id.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def create_item(self, club_id: int, plan_id: int, data: dict) -> WorkoutPlanItem:
        self.get_plan(club_id=club_id, plan_id=plan_id)

        item = WorkoutPlanItem(plan_id=plan_id, **data)
        self.db.add(item)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # uq_workout_plan_items_plan_week_day_order
            raise ConflictError("WorkoutPlanItem conflict") from e
        self.db.refresh(item)
        return item

    def get_item(self, club_id: int, plan_id: int, item_id: int) -> WorkoutPlanItem:
        # club scope enforced by plan lookup AND plan_id binding
        self.get_plan(club_id=club_id, plan_id=plan_id)

        stmt = select(WorkoutPlanItem).where(
            WorkoutPlanItem.plan_id == plan_id,
            WorkoutPlanItem.id == item_id,
        )
        item = self.db.execute(stmt).scalars().first()
        if not item:
            raise WorkoutNotFoundError("WorkoutPlanItem not found")
        return item

    def update_item(self, club_id: int, plan_id: int, item_id: int, patch: dict) -> WorkoutPlanItem:
        item = self.get_item(club_id=club_id, plan_id=plan_id, item_id=item_id)
        for k, v in patch.items():
            setattr(item, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("WorkoutPlanItem conflict") from e
        self.db.refresh(item)
        return item

    def delete_item(self, club_id: int, plan_id: int, item_id: int) -> None:
        item = self.get_item(club_id=club_id, plan_id=plan_id, item_id=item_id)
        self.db.delete(item)
        self.db.commit()

    # -------------------------
    # Exercises (club-scoped via join chain plan->item->exercise)
    # -------------------------

    def list_exercises(self, club_id: int, plan_id: int, item_id: int) -> Sequence[WorkoutPlanExercise]:
        # ensures club scope via plan + item binding
        self.get_item(club_id=club_id, plan_id=plan_id, item_id=item_id)

        stmt = (
            select(WorkoutPlanExercise)
            .where(WorkoutPlanExercise.item_id == item_id)
            .order_by(WorkoutPlanExercise.position.asc(), WorkoutPlanExercise.id.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def create_exercise(self, club_id: int, plan_id: int, item_id: int, data: dict) -> WorkoutPlanExercise:
        self.get_item(club_id=club_id, plan_id=plan_id, item_id=item_id)

        ex = WorkoutPlanExercise(item_id=item_id, **data)
        self.db.add(ex)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # uq_workout_plan_exercises_item_position
            raise ConflictError("WorkoutPlanExercise conflict") from e
        self.db.refresh(ex)
        return ex

    def get_exercise(self, club_id: int, plan_id: int, item_id: int, exercise_id: int) -> WorkoutPlanExercise:
        self.get_item(club_id=club_id, plan_id=plan_id, item_id=item_id)

        stmt = select(WorkoutPlanExercise).where(
            WorkoutPlanExercise.item_id == item_id,
            WorkoutPlanExercise.id == exercise_id,
        )
        ex = self.db.execute(stmt).scalars().first()
        if not ex:
            raise WorkoutNotFoundError("WorkoutPlanExercise not found")
        return ex

    def update_exercise(
        self,
        club_id: int,
        plan_id: int,
        item_id: int,
        exercise_id: int,
        patch: dict,
    ) -> WorkoutPlanExercise:
        ex = self.get_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
        )
        for k, v in patch.items():
            setattr(ex, k, v)

        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("WorkoutPlanExercise conflict") from e

        self.db.refresh(ex)
        return ex

    def delete_exercise(self, club_id: int, plan_id: int, item_id: int, exercise_id: int) -> None:
        ex = self.get_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
        )
        self.db.delete(ex)
        self.db.commit()
