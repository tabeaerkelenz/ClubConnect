from __future__ import annotations

from app.repositories.workout_plan import WorkoutPlanRepository

from app.services.membership import MembershipService
from app.models.models import MembershipRole

from app.exceptions.base import CoachOrOwnerRequiredError


class WorkoutPlanService:
    """
    Access rules (server-side):
    - Read (list/get/nested/items/exercises list): any club member
    - Create plan: any club member (created_by_id = current user)
    - Update/Delete plan + Items/Exercises write:
        - coach/owner: allowed for any plan
        - athlete/member: only allowed if plan.created_by_id == user_id
    """

    def __init__(self, repo: WorkoutPlanRepository, membership_service: MembershipService):
        self.repo = repo
        self.membership_service = membership_service

    # -------------------------
    # Access helpers
    # -------------------------

    def _require_read(self, club_id: int, user_id: int) -> None:
        # member or higher
        self.membership_service.require_member_of_club(club_id=club_id, user_id=user_id)

    def _require_write_plan(self, club_id: int, user_id: int, plan) -> None:
        """
        Allow write if:
        - coach/owner in that club
        - OR plan.created_by_id == user_id
        """
        membership = self.membership_service.get_membership_for_user_in_club(club_id=club_id, user_id=user_id)

        if membership.role in {MembershipRole.coach, MembershipRole.owner}:
            return

        if getattr(plan, "created_by_id", None) == user_id:
            return

        raise CoachOrOwnerRequiredError("You are not allowed to modify this workout plan")

    # -------------------------
    # Plans
    # -------------------------

    def list_plans(self, club_id: int, user_id: int):
        self._require_read(club_id, user_id)
        return self.repo.list_plans(club_id)

    def create_plan(self, club_id: int, user_id: int, data: dict):
        # Athletes/members are allowed to create their own plans
        self._require_read(club_id, user_id)
        return self.repo.create_plan(club_id=club_id, created_by_id=user_id, data=data)

    def get_plan(self, club_id: int, plan_id: int, user_id: int, nested: bool = False):
        self._require_read(club_id, user_id)
        if nested:
            return self.repo.get_plan_nested(club_id=club_id, plan_id=plan_id)
        return self.repo.get_plan(club_id=club_id, plan_id=plan_id)

    def update_plan(self, club_id: int, plan_id: int, user_id: int, patch: dict):
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        return self.repo.update_plan(club_id=club_id, plan_id=plan_id, patch=patch)

    def delete_plan(self, club_id: int, plan_id: int, user_id: int) -> None:
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        self.repo.delete_plan(club_id=club_id, plan_id=plan_id)

    # -------------------------
    # Items (read is member, write is plan-owner/coach)
    # -------------------------

    def list_items(self, club_id: int, plan_id: int, user_id: int):
        self._require_read(club_id, user_id)
        return self.repo.list_items(club_id=club_id, plan_id=plan_id)

    def create_item(self, club_id: int, plan_id: int, user_id: int, data: dict):
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        return self.repo.create_item(club_id=club_id, plan_id=plan_id, data=data)

    def update_item(self, club_id: int, plan_id: int, item_id: int, user_id: int, patch: dict):
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        return self.repo.update_item(club_id=club_id, plan_id=plan_id, item_id=item_id,patch=patch)

    def delete_item(self, club_id: int, plan_id: int, item_id: int, user_id: int) -> None:
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        self.repo.delete_item(club_id=club_id, plan_id=plan_id, item_id=item_id)

    # -------------------------
    # Exercises (read is member, write is plan-owner/coach)
    # -------------------------

    def list_exercises(self, club_id: int, plan_id: int, item_id: int, user_id: int):
        self._require_read(club_id, user_id)
        return self.repo.list_exercises(club_id=club_id, plan_id=plan_id, item_id=item_id)

    def create_exercise(self, club_id: int, plan_id: int, item_id: int, user_id: int, data: dict):
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        return self.repo.create_exercise(club_id=club_id, plan_id=plan_id, item_id=item_id, data=data)

    def update_exercise(
        self,
        club_id: int,
        plan_id: int,
        item_id: int,
        exercise_id: int,
        user_id: int,
        patch: dict,
    ):
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        return self.repo.update_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
            patch=patch,
        )

    def delete_exercise(self, club_id: int, plan_id: int, item_id: int, exercise_id: int, user_id: int) -> None:
        plan = self.repo.get_plan(club_id=club_id, plan_id=plan_id)
        self._require_write_plan(club_id, user_id, plan)
        self.repo.delete_exercise(
            club_id=club_id,
            plan_id=plan_id,
            item_id=item_id,
            exercise_id=exercise_id,
        )