from __future__ import annotations
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Plan, Membership, PlanAssignee

class PlanNotFound(Exception):
    pass


class PlanAssigneeNotFound(Exception):
    pass


class UserNotClubMember(Exception):
    pass


class Conflict(Exception):
    pass


def _require_plan_in_club(db: Session, club_id: int, plan_id: int) -> Plan:
    """Helper to get a plan by ID within a club or raise 404 if not found."""
    plan = db.get(Plan, plan_id)
    if not plan or plan.club_id != club_id:
        raise PlanNotFound(f"plan {plan_id} not in club {club_id}")
    return plan


def _require_user_is_member_of_club(db: Session, club_id: int, user_id: int) -> None:
    """Helper to ensure a user is a member of a club or raise."""
    member = db.execute(
        sa.select(Membership).where(
            Membership.club_id == club_id,
            Membership.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not member:
        raise UserNotClubMember(f"user {user_id} is not a member of club {club_id}")


def list_assignees(db: Session, club_id: int, plan_id: int, me) -> list[PlanAssignee]:
    """List all assignees for a plan in a club."""
    _require_plan_in_club(db, club_id, plan_id)
    stmt = (
        sa.select(PlanAssignee)
        .where(PlanAssignee.plan_id == plan_id)
        .order_by(PlanAssignee.created_at.asc())
    )
    return db.execute(stmt).scalars().all()


def add_assignee(db: Session, club_id: int, plan_id: int, me, data) -> PlanAssignee:
    """Add an assignee to a plan in a club."""
    _require_plan_in_club(db, club_id, plan_id)
    _require_user_is_member_of_club(db, club_id, data.user_id)

    obj = PlanAssignee(
        plan_id=plan_id,
        user_id=data.user_id,
        role=data.role,  # "coach" | "athlete"
        assigned_by_id=me.id,
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # 23505 = unique_violation (plan_id, user_id) already exists
        if getattr(getattr(e, "orig", None), "pgcode", None) == "23505":
            raise Conflict("assignee already exists for this plan")
        raise
    db.refresh(obj)
    return obj


def remove_assignee(
    db: Session, club_id: int, plan_id: int, assignee_id: int, me
) -> None:
    """Remove an assignee from a plan in a club."""
    _require_plan_in_club(db, club_id, plan_id)
    obj = db.get(PlanAssignee, assignee_id)
    if not obj or obj.plan_id != plan_id:
        raise PlanAssigneeNotFound(f"assignee {assignee_id} not in plan {plan_id}")
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict("could not delete assignee")
