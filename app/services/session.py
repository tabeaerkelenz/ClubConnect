# python
from typing import List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession

from app.auth.membership_deps import assert_is_coach_or_owner_of_club
from app.crud.plan_assignment import Conflict
from app.crud.session import (
    list_sessions,
    update_session,
    delete_session, get_session_in_plan_and_club, insert_session,
)
from app.db.models import User
from app.exceptions.base import SessionNotFound, InvalidTimeRange
from app.schemas.session import SessionCreate


def list_sessions_service(db: SASession, club_id: int, plan_id: int, me: User) -> List:
    return list_sessions(db, club_id=club_id, plan_id=plan_id, me=me)


def create_session_service(
    db: SASession, club_id: int, plan_id: int, me: User, data: SessionCreate
):
    try:
        session =  insert_session(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
        db.commit()
        db.refresh(session)
    except IntegrityError as e:
        raise


def get_session_service(db, club_id: int, plan_id: int, session_id: int, me: User):
    session = get_session_in_plan_and_club(db, club_id=club_id, plan_id=plan_id, session_id=session_id, me=me)
    if not session:
        raise SessionNotFound()
    return session


def update_session_service(db, club_id, plan_id, session_id, me, data):
    assert_is_coach_or_owner_of_club(db, user_id=club_id, club_id=club_id)
    session = get_session_service(db, club_id, plan_id, session_id, me)

    # Validate time range before mutating
    if data.starts_at and data.ends_at and data.starts_at >= data.ends_at:
        raise InvalidTimeRange()

    updates = data.model_dump(exclude_unset=True)
    new_starts = updates.get("starts_at", getattr(session, "starts_at"))
    new_ends = updates.get("ends_at", getattr(session, "ends_at"))

    if new_starts and new_ends and new_starts >= new_ends:
            raise InvalidTimeRange()
    try:
        update_session(db, session_id=session_id, **updates)
        db.commit()
        db.refresh(session)
        return session
    except IntegrityError as e:
        db.rollback()
        raise Conflict() from e


def delete_session_service(
    db: SASession, club_id: int, plan_id: int, session_id: int, me: User
):
    assert_is_coach_or_owner_of_club(db, user_id=club_id, club_id=club_id)
    session = get_session_service(db, club_id, plan_id, session_id, me)
    try:
        delete_session(db, session)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise Conflict() from e
