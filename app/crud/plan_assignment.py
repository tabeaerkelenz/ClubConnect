from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Plan, Membership, PlanAssignee



def get_plan_in_club(db: Session, club_id: int, plan_id: int) -> Plan | None:
    stmt = sa.select(Plan).where(Plan.id == plan_id, Plan.club_id == club_id)
    return db.execute(stmt).scalar_one_or_none()


def list_assignees(db: Session, plan_id: int) -> list[PlanAssignee]:
    stmt = (
        sa.select(PlanAssignee)
        .where(PlanAssignee.plan_id == plan_id)
        .order_by(PlanAssignee.created_at.asc(), PlanAssignee.id.asc())
    )
    return db.execute(stmt).scalars().all()


def add_assignee(db: Session, *, plan_id: int, user_id: int, role: str, assigned_by_id: int) -> PlanAssignee:
    assignment = PlanAssignee(
        plan_id=plan_id,
        user_id=user_id,
        role=role,
        assigned_by_id=assigned_by_id,
    )
    db.add(assignment)
    db.flush()     # get obj.id set
    return assignment



def get_assignee(db: Session, assignee_id: int) -> PlanAssignee | None:
    return db.get(PlanAssignee, assignee_id)


def delete_assignee(db: Session, obj: PlanAssignee) -> None:
    db.delete(obj)
    db.flush()
