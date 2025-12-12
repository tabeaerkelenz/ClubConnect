from typing import List, Optional

from app.models.models import User, Plan
from app.repositories.plan import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate
from app.services.membership import MembershipService
from app.models.models import PlanAssigneeRole


class PlanService:
    """Business logic for plans.

    - No DB session, no FastAPI.
    - Delegates persistence to PlanRepository.
    - Delegates membership/role checks to MembershipService.
    """

    def __init__(
        self,
        plan_repo: PlanRepository,
        membership_service: MembershipService,
    ) -> None:
        self.plan_repo = plan_repo
        self.membership_service = membership_service

    # ---- internal helpers ----

    def _ensure_member(self, *, club_id: int, me: User) -> None:
        """Raise NotClubMemberError if user is not in club."""
        self.membership_service.require_member_of_club(
            user_id=me.id, club_id=club_id
        )

    def _ensure_coach_or_owner(self, *, club_id: int, me: User) -> None:
        """Raise NotCoachOfClubError if user is not coach/owner in club."""
        self.membership_service.require_coach_or_owner_of_club(
            user_id=me.id, club_id=club_id
        )

    def _parse_role(self, role_str: Optional[str]) -> Optional[PlanAssigneeRole]:
        """Map query strings ('owner', 'coach', 'athlete', 'member') to PlanAssigneeRole or None."""
        if role_str is None:
            return None

        # Accept "member" as alias for athlete
        mapping = {
            "owner": PlanAssigneeRole.owner,
            "coach": PlanAssigneeRole.coach,
            "athlete": PlanAssigneeRole.athlete,
            "member": PlanAssigneeRole.athlete,
        }
        try:
            return mapping[role_str]
        except KeyError:
            # Unknown role string → simply no results (handled in list_assigned_plans)
            return None

    # ---- queries ----

    def list_plans_for_club(self, *, club_id: int, me: User) -> List[Plan]:
        """List all plans in a club, visible to any club member."""
        self._ensure_member(club_id=club_id, me=me)
        return self.plan_repo.list_plans_for_club(club_id=club_id)

    def list_assigned_plans(
        self,
        *,
        club_id: int,
        me: User,
        role: Optional[str] = None,
    ) -> List[Plan]:
        """List plans assigned to the current user, optionally filtered by role."""
        self._ensure_member(club_id=club_id, me=me)

        role_enum = self._parse_role(role)

        if role is not None and role_enum is None:
            # Unknown role string → return empty list
            return []

        return self.plan_repo.list_assigned_plans(
            club_id=club_id,
            user_id=me.id,
            role=role_enum,
        )

    def get_plan(self, *, club_id: int, plan_id: int, me: User) -> Plan:
        """Get a single plan by id in a club."""
        self._ensure_member(club_id=club_id, me=me)
        # repo handles PlanNotFoundError
        return self.plan_repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)

    # ---- mutations ----

    def create_plan(
        self,
        *,
        club_id: int,
        me: User,
        data: PlanCreate,
    ) -> Plan:
        """Create a new plan - only coach/owner allowed."""
        self._ensure_member(club_id=club_id, me=me)
        return self.plan_repo.create_plan(
            club_id=club_id, created_by_id=me.id, data=data
        )

    def update_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        me: User,
        data: PlanUpdate,
    ) -> Plan:
        """Update plan details within a club."""
        self._ensure_coach_or_owner(club_id=club_id, me=me)

        # get first (raises PlanNotFoundError if missing)
        plan = self.plan_repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)
        # then persist
        return self.plan_repo.update_plan(plan=plan, data=data)

    def delete_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        me: User,
    ) -> None:
        """Delete a plan from a club."""
        self._ensure_coach_or_owner(club_id=club_id, me=me)

        plan = self.plan_repo.get_plan_in_club(club_id=club_id, plan_id=plan_id)
        self.plan_repo.delete_plan(plan=plan)
