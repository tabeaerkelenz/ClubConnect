from typing import List
from sqlalchemy.orm import Session
from app.crud.plan import (
    create_plan,
    get_plan,
    get_plans,
    list_assigned_plans,
    update_plan,
    delete_plan,
)
from app.db.models import User
from app.exceptions.plan import NotCoachOfClubError, PlanNotFoundError
from app.schemas.plan import PlanCreate, PlanUpdate

def create_plan_service(db: Session, club_id: int, me: User, data: PlanCreate):
    try:
        return create_plan(db, club_id=club_id, user_id=me.id, data=data)
    except NotCoachOfClubError:
        raise
    except Exception as e:
        raise

def get_plan_service(db: Session, club_id: int, plan_id: int, me: User):
    try:
        return get_plan(db, club_id=club_id, plan_id=plan_id, me=me)
    except PlanNotFoundError:
        raise

def get_plans_service(db: Session, club_id: int, me: User) -> List:
    return get_plans(db, club_id=club_id, me=me)

def list_assigned_plans_service(db: Session, club_id: int, me: User, role: str = None):
    return list_assigned_plans(db, club_id=club_id, me=me, role=role)

def update_plan_service(db: Session, club_id: int, plan_id: int, me: User, data: PlanUpdate):
    try:
        return update_plan(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
    except NotCoachOfClubError:
        raise
    except PlanNotFoundError:
        raise

def delete_plan_service(db: Session, club_id: int, plan_id: int, me: User):
    try:
        delete_plan(db, club_id=club_id, plan_id=plan_id, me=me)
    except NotCoachOfClubError:
        raise
    except PlanNotFoundError:
        raise
