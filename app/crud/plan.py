from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.membership_asserts import assert_is_coach_of_club, assert_is_member_of_club
from app.db.models import PlanType, Plan, User, PlanAssignee, PlanAssigneeRole
from app.schemas.plan import PlanCreate, PlanUpdate

def create_plan(db: Session, *, club_id: int, user_id: int, data: PlanCreate) -> Plan:
    plan = Plan(
        name=data.name,
        plan_type=data.plan_type,
        description=data.description,
        club_id=club_id,
        created_by_id=user_id,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def _get_plan_in_club_or_404(db, club_id: int, plan_id: int):
    stmt = select(Plan).where(Plan.club_id == club_id, Plan.id == plan_id)
    plan = db.execute(stmt).scalar_one_or_none()
    return plan


def get_plan(db: Session, *, club_id: int, plan_id: int, me: User) -> Plan:
    return _get_plan_in_club_or_404(db, club_id, plan_id)

def get_plans(db: Session, *, club_id: int, me: User) -> List[Plan]:
    stmt = select(Plan).where(Plan.club_id == club_id).order_by(Plan.name.asc())
    return db.execute(stmt).scalars().all()

def list_assigned_plans(db, club_id: int, me, role: str | PlanAssigneeRole) -> list[Plan]:
    stmt = (
        select(Plan)
        .join(PlanAssignee, PlanAssignee.plan_id == Plan.id)
        .where(Plan.club_id == club_id, PlanAssignee.user_id == me.id)
        .order_by(Plan.name.asc())
    )
    if role:
        # accept "member" as alias for athlete (optional)
        if isinstance(role, str):
            role_map = {"member": "athlete", "athlete": "athlete", "coach": "coach"}
            try:
                role = PlanAssigneeRole(role_map.get(role, role))
            except ValueError:
                # invalid role string -> no rows; alternatively raise
                return []
        stmt = stmt.where(PlanAssignee.role == role)

    return db.execute(stmt).scalars().all()

def update_plan(db: Session, *, club_id: int, plan_id: int, me: User, data: PlanUpdate) -> Plan:
    plan = _get_plan_in_club_or_404(db, club_id, plan_id)
    payload = data.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan

def delete_plan(db: Session, *, club_id: int, plan_id: int, me: User) -> None:
    plan = _get_plan_in_club_or_404(db, club_id, plan_id)
    db.delete(plan)
    db.commit()
