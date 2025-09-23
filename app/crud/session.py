from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

# update other table crud alswell to SASession and import sqlalchemy as sa
from sqlalchemy.orm import Session as SASession

# adjust import to your layout
from app.db.models import Session as SessionModel, Plan

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
    """Get plan by id and club_id or raise SessionNotFound."""
    stmt = sa.select(Plan).where(
        Plan.id == plan_id,
        Plan.club_id == club_id,
    )
    plan = db.execute(stmt).scalar_one_or_none()
    if not plan:
        raise SessionNotFound()
    return plan


def _get_session_in_plan_and_club_or_raise(
    db: SASession, club_id: int, plan_id: int, session_id: int
) -> SessionModel:
    """Get session by id, plan_id and club_id or raise SessionNotFound."""
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
    """List all sessions in a plan within a club."""""
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    stmt = (
        sa.select(SessionModel)
        .where(SessionModel.plan_id == plan_id)
        .order_by(SessionModel.starts_at.asc(), SessionModel.id.asc())
    )
    return db.execute(stmt).scalars().all()


def create_session(db: SASession, club_id: int, plan_id: int, me, data) -> SessionModel:
    """Create a new session in a plan within a club."""
    # Ensure the parent Plan belongs to the club
    _get_plan_in_club_or_raise(db, club_id, plan_id)

    payload = data.model_dump()
    obj = SessionModel(
        plan_id=plan_id,
        name=payload["name"],
        description=payload["description"],
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
    """Get a session by ID within a plan and club, ensuring it exists."""
    return _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)


def update_session(
    db: SASession, club_id: int, plan_id: int, session_id: int, me, data
) -> SessionModel:
    """Update a session by ID within a plan and club."""
    session = _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)

    updates = data.model_dump(exclude_unset=True)
    for k, v in updates.items():
        setattr(session, k, v)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict()
    db.refresh(session)
    return session


def delete_session(
    db: SASession, club_id: int, plan_id: int, session_id: int, me
) -> None:
    """Delete a session by ID within a plan and club."""
    obj = _get_session_in_plan_and_club_or_raise(db, club_id, plan_id, session_id)
    db.delete(obj)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise Conflict()
    return None
