from sqlalchemy.orm import Session
from app.crud.plan_assignment import (
    list_assignees,
    add_assignee,
    remove_assignee,
    PlanNotFound,
    PlanAssigneeNotFound,
    UserNotClubMember,
    Conflict,
)

def list_assignees_service(db: Session, club_id: int, plan_id: int, me):
    try:
        return list_assignees(db, club_id, plan_id, me)
    except PlanNotFound:
        raise
    except UserNotClubMember:
        raise

def add_assignee_service(db: Session, club_id: int, plan_id: int, me, data):
    try:
        return add_assignee(db, club_id, plan_id, me, data)
    except (PlanNotFound, UserNotClubMember, Conflict) as e:
        raise

def remove_assignee_service(db: Session, club_id: int, plan_id: int, assignee_id: int, me):
    try:
        return remove_assignee(db, club_id, plan_id, assignee_id, me)
    except (PlanNotFound, PlanAssigneeNotFound, Conflict) as e:
        raise
