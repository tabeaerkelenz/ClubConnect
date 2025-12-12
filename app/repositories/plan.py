from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession

from app.models.models import Plan, PlanAssignee, PlanAssigneeRole
from app.exceptions.base import PlanNotFoundError, PlanNameExistsError
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanRepository:
    """Persistence layer for Plan entities.

    - Owns the SQLAlchemy session.
    - Performs all queries, inserts, updates, deletes.
    - Maps not-found and integrity issues to domain errors.
    - Contains NO business rules or auth/role logic.
    """

    def __init__(self, db: SASession) -> None:
        self.db = db


    # ---- Helpers ----
    def _get_plan_in_club_or_raise(self, club_id: int, plan_id: int) -> Plan:
        stmt = select(Plan).where(Plan.club_id == club_id, Plan.id == plan_id)
        plan = self.db.execute(stmt).scalar_one_or_none()
        if plan is None:
            raise PlanNotFoundError(f"Plan {plan_id} in club {club_id} not found")
        return plan


    # ---- create, read, update, delete ----
    def create_plan(
        self, *, club_id: int, created_by_id: int, data: PlanCreate
    ) -> Plan:
        """Create a new plan in a club."""
        plan = Plan(
            name=data.name,
            plan_type=data.plan_type,
            description=data.description,
            club_id=club_id,
            created_by_id=created_by_id,
        )
        self.db.add(plan)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            # Optional: inspect exc.orig / string to detect unique violations
            # For now we assume a (club_id, name) uniqueness mapped to PlanNameExistsError
            raise PlanNameExistsError(
                f"A plan named '{data.name}' already exists in this club."
            ) from exc
        self.db.refresh(plan)
        return plan

    def get_plan_in_club(self, *, club_id: int, plan_id: int) -> Plan:
        """Get a plan by ID within a club, or raise PlanNotFoundError."""
        return self._get_plan_in_club_or_raise(club_id, plan_id)

    def list_plans_for_club(self, *, club_id: int) -> List[Plan]:
        """List all plans in a club, ordered by name."""
        stmt = select(Plan).where(Plan.club_id == club_id).order_by(Plan.name.asc())
        return list(self.db.execute(stmt).scalars().all())

    def list_assigned_plans(
        self,
        *,
        club_id: int,
        user_id: int,
        role: Optional[PlanAssigneeRole] = None,
    ) -> List[Plan]:
        """
        List all plans in a club assigned to the given user,
        optionally filtered by PlanAssigneeRole.
        """
        stmt = (
            select(Plan)
            .join(PlanAssignee, PlanAssignee.plan_id == Plan.id)
            .where(Plan.club_id == club_id, PlanAssignee.user_id == user_id)
            .order_by(Plan.name.asc())
        )

        if role is not None:
            stmt = stmt.where(PlanAssignee.role == role)

        return list(self.db.execute(stmt).scalars().all())

    def update_plan(self, plan: Plan, data: PlanUpdate) -> Plan:
        """Update a plan's details within a club."""
        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(plan, field, value)

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if "uq_plans_club_name" in str(exc.orig):
                raise PlanNameExistsError(
                    f"A plan named '{payload.get('name')}' already exists in this club."
                ) from exc
            raise

        self.db.refresh(plan)
        return plan

    def delete_plan(self, plan: Plan) -> None:
        """Delete a plan by ID within a club."""
        self.db.delete(plan)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            # Maby want a "PlanInUseError" later
            raise
