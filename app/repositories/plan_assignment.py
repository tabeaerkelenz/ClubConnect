from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Plan, PlanAssignee, PlanAssigneeRole
from app.exceptions.base import PlanNotFoundError, PlanAssignmentExistsError

class PlanAssignmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_plan_in_club(self, *, club_id: int, plan_id: int) -> Plan:
        stmt = sa.select(Plan).where(Plan.id == plan_id, Plan.club_id == club_id)
        plan = self.db.execute(stmt).scalar_one_or_none()
        if not plan:
            raise PlanNotFoundError()
        return plan

    def list_for_plan(self, *, plan_id: int) -> list[PlanAssignee]:
        stmt = (
            sa.select(PlanAssignee)
            .where(PlanAssignee.plan_id == plan_id)
            .order_by(PlanAssignee.created_at.asc(), PlanAssignee.id.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def create_user_assignee(
        self,
        *,
        plan_id: int,
        user_id: int,
        role: PlanAssigneeRole,
        assigned_by_id: int,
    ) -> PlanAssignee:
        obj = PlanAssignee(
            plan_id=plan_id,
            user_id=user_id,
            group_id=None,
            role=role,
            assigned_by_id=assigned_by_id,
        )
        self.db.add(obj)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise PlanAssignmentExistsError() from e
        self.db.refresh(obj)
        return obj

    def get(self, *, assignee_id: int) -> PlanAssignee | None:
        return self.db.get(PlanAssignee, assignee_id)

    def delete(self, obj: PlanAssignee) -> None:
        self.db.delete(obj)
        self.db.commit()
