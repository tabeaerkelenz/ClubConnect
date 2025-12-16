from __future__ import annotations

from app.repositories.plan_assignment import PlanAssignmentRepository
from app.services.membership import MembershipService
from app.schemas.plan_assignment import PlanAssigneeCreate
from app.exceptions.base import PlanAssigneeNotFound, UserNotClubMember

class PlanAssignmentService:
    def __init__(self, repo: PlanAssignmentRepository, membership_service: MembershipService) -> None:
        self.repo = repo
        self.memberships = membership_service

    def list_assignees(self, *, club_id: int, plan_id: int, me_id: int):
        self.memberships.require_member_of_club(me_id, club_id)
        self.repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)
        return self.repo.list_for_plan(plan_id=plan_id)

    def add_assignee(self, *, club_id: int, plan_id: int, me_id: int, data: PlanAssigneeCreate):
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        self.repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)

        # user-assignees only for now:
        try:
            self.memberships.require_member_of_club(data.user_id, club_id)
        except Exception:
            raise UserNotClubMember()

        return self.repo.create_user_assignee(
            plan_id=plan_id,
            user_id=data.user_id,
            role=data.role,
            assigned_by_id=me_id,
        )

    def remove_assignee(self, *, club_id: int, plan_id: int, assignee_id: int, me_id: int) -> None:
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        self.repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)

        obj = self.repo.get(assignee_id=assignee_id)
        if not obj or obj.plan_id != plan_id:
            raise PlanAssigneeNotFound()

        self.repo.delete(obj)
