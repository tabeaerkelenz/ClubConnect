from __future__ import annotations

from app.repositories.exercise import ExerciseRepository
from app.services.membership import MembershipService
from app.schemas.exercise import ExerciseCreate, ExerciseUpdate


class ExerciseService:
    def __init__(
        self,
        exercise_repo: ExerciseRepository,
        membership_service: MembershipService,
    ):
        self.exercise_repo = exercise_repo
        self.membership_service = membership_service

    def list_exercises(self, *, club_id: int, plan_id: int, user_id: int):
        self.membership_service.require_member_of_club(club_id=club_id, user_id=user_id)
        return self.exercise_repo.list_in_plan(club_id=club_id, plan_id=plan_id)

    def get_exercise(self, *, club_id: int, plan_id: int, exercise_id: int, user_id: int):
        self.membership_service.require_member_of_club(club_id=club_id, user_id=user_id)
        return self.exercise_repo.get_in_plan(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )

    def create_exercise(self, *, club_id: int, plan_id: int, user_id: int, data: ExerciseCreate):
        self.membership_service.require_coach_or_owner_of_club(club_id=club_id, user_id=user_id)

        return self.exercise_repo.create_in_plan(
            club_id=club_id,
            plan_id=plan_id,
            name=data.name,
            description=data.description,
            sets=data.sets,
            repetitions=data.repetitions,
            position=data.position,
            day_label=data.day_label,
        )

    def update_exercise(
        self,
        *,
        club_id: int,
        plan_id: int,
        exercise_id: int,
        user_id: int,
        data: ExerciseUpdate,
    ):
        self.membership_service.require_coach_or_owner_of_club(club_id=club_id, user_id=user_id)

        updates = data.model_dump(exclude_unset=True)

        # protect: don't allow "position": None to overwrite existing position
        if updates.get("position") is None:
            updates.pop("position", None)

        return self.exercise_repo.update_in_plan(
            club_id=club_id,
            plan_id=plan_id,
            exercise_id=exercise_id,
            updates=updates,
        )

    def delete_exercise(self, *, club_id: int, plan_id: int, exercise_id: int, user_id: int) -> None:
        self.membership_service.require_coach_or_owner_of_club(club_id=club_id, user_id=user_id)
        self.exercise_repo.delete_in_plan(
            club_id=club_id, plan_id=plan_id, exercise_id=exercise_id
        )
