from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.exceptions import Conflict

from app.auth.membership_deps import assert_has_any_role_of_club, assert_is_coach_or_owner_of_club
from app.exceptions.base import PlanNotFoundError, PlanAssignmentExistsError, PlanAssigneeNotFound
from app.crud.plan_assignment import list_assignees, add_assignee, get_plan_in_club, get_assignee, delete_assignee


def list_assignees_service(db: Session, club_id: int, plan_id: int, me):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()
    assert_has_any_role_of_club()
    return list_assignees(db, plan_id)


def add_assignee_service(db: Session, club_id: int, plan_id: int, me, data):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()

    assert_is_coach_or_owner_of_club(db, club_id, plan_id)
    try:
        assignment = add_assignee(
            db,
            plan_id=plan_id,
            user_id=data.user_id,
            role=data.role,
            assigned_by_id=me.id,
        )
        db.commit()
        db.refresh(assignment)
        return assignment
    except IntegrityError as e:
        db.rollback()
        raise PlanAssignmentExistsError from e


def remove_assignee_service(db: Session, club_id: int, plan_id: int, assignee_id: int, me):
    plan = get_plan_in_club(db, club_id, plan_id)
    if not plan:
        raise PlanNotFoundError()

    assert_is_coach_or_owner_of_club(db, club_id, plan_id)

    assignment = get_assignee(db, assignee_id)
    if not assignment or assignment.plan_id != plan_id:
        raise PlanAssigneeNotFound()

    delete_assignee(db, assignment)
    db.commit()
    return None
