# python
from typing import List
from sqlalchemy.orm import Session as SASession
from app.crud.session import (
    list_sessions,
    create_session,
    get_session,
    update_session,
    delete_session,
    SessionNotFound,
    Conflict,
    InvalidTimeRange,
    NotClubMember,
    NotCoach,
)
from app.db.models import User
from app.schemas.session import SessionCreate, SessionUpdate


def list_sessions_service(db: SASession, club_id: int, plan_id: int, me: User) -> List:
    return list_sessions(db, club_id=club_id, plan_id=plan_id, me=me)


def create_session_service(
    db: SASession, club_id: int, plan_id: int, me: User, data: SessionCreate
):
    try:
        return create_session(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
    except (Conflict, InvalidTimeRange, NotClubMember, NotCoach) as e:
        raise


def get_session_service(
    db: SASession, club_id: int, plan_id: int, session_id: int, me: User
):
    try:
        return get_session(
            db, club_id=club_id, plan_id=plan_id, session_id=session_id, me=me
        )
    except SessionNotFound:
        raise


def update_session_service(
    db: SASession,
    club_id: int,
    plan_id: int,
    session_id: int,
    me: User,
    data: SessionUpdate,
):
    try:
        return update_session(
            db,
            club_id=club_id,
            plan_id=plan_id,
            session_id=session_id,
            me=me,
            data=data,
        )
    except (Conflict, SessionNotFound, InvalidTimeRange, NotCoach) as e:
        raise


def delete_session_service(
    db: SASession, club_id: int, plan_id: int, session_id: int, me: User
):
    try:
        return delete_session(
            db, club_id=club_id, plan_id=plan_id, session_id=session_id, me=me
        )
    except (Conflict, SessionNotFound, NotCoach) as e:
        raise
