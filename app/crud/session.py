from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession     # update other table crud alswell to SASession and import sqlalchemy as sa

from ClubConnect.app.db.models import Session as SessionModel, Plan  # adjust import to your layout

# --- Domain errors (no HTTP here) ---
class SessionNotFound(Exception):
    """Cant find the session"""
    pass
class Conflict(Exception):
    """Conflict (e.g., unique constraint)."""
    pass
class InvalidTimeRange(Exception):
    """starts_at must be before ends_at."""
    pass
class NotClubMember(Exception):
    """User is not a member of this club."""
    pass
class NotCoach(Exception):
    """Coach role required for this action."""
    pass

# --- Internal helpers ---

def _get_plan_in_club_or_raise(db: SASession, club_id: int, plan_id: int) -> Plan:
    stmt = sa.select(Plan).where(
        Plan.id == plan_id,
        Plan.club_id == club_id,
    )
    plan = db.execute(stmt).scalar_one_or_none()
    if not plan:
        # We reuse SessionNotFound to keep errors local to this module,
        # but you can define PlanNotFound in a plans.py if you prefer.
        raise SessionNotFound()
    return plan


def _get_session_in_plan_and_club_or_raise(
    db: SASession, club_id: int, plan_id: int, session_id: int
) -> SessionModel:
    # Ensure the session belongs to the given plan AND that plan belongs to the club
    stmt = (
        sa.select(SessionModel)
        .join(Plan, Plan.id == SessionModel.plan_id)
        .where(
            SessionModel.id == session_id,
            SessionModel.plan_id == plan_id,
            Plan.club_id == club_id,
        )
    )
    session = db.execute(stmt).scalar_one_or_none()
    if not session:
        raise SessionNotFound()
    return session


# --- CRUD ---

def list_sessions(db: SASession, club_id: int, plan_id: int, me) -> list[SessionModel]:
    # Guard checks (membership) happen in the router via your assert_* functions.
    # We still enforce cross-club here.
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    stmt = (
        sa.select(SessionModel)
        .where(SessionModel.plan_id == plan_id)
        .order_by(SessionModel.starts_at.asc(), SessionModel.id.asc())
    )
    return db.execute(stmt).scalars().all()


def create_session(
    db: SASession, club_id: int, plan_id: int, me, data
) -> SessionModel:
    # Ensure the parent Plan belongs to the club
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    payload = data.model_dump()
    obj = SessionModel(
        plan_id=plan_id,
        starts_at=payload["starts_at"],
        ends_at=payload["ends_at"],
        location=payload["location"],
        note=payload.get("note"),
        created_by=me.id,  # server-controlled
    )
    db.add(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict()
    db.refresh(obj)
    return obj


def get_session(
    db: SASession, club_id: int, plan_id: int, session_id: int, me
) -> SessionModel:
    return _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)


def update_session(
    db: SASession, club_id: int, plan_id: int, session_id: int, me, data
) -> SessionModel:
    obj = _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)

    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(obj, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict()
    db.refresh(obj)
    return obj


def delete_session(
    db: SASession, club_id: int, plan_id: int, session_id: int, me
) -> None:
    obj = _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict()
    return None
