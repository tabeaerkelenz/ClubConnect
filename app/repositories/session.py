from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session as SASession, Session

from app.models.models import Session as SessionModel, Plan

def get_session_club_id(db: Session, session_id: int) -> int | None:
    return db.execute(
        select(Plan.club_id)
        .join(SessionModel, SessionModel.plan_id == Plan.id)
        .where(SessionModel.id == session_id)
    ).scalar_one_or_none()


def get_plan_in_club(db: SASession, club_id: int, plan_id: int) -> Plan:
    stmt = sa.select(Plan).where(
        Plan.id == plan_id,
        Plan.club_id == club_id,
    )
    plan = db.execute(stmt).scalar_one_or_none()
    return plan


def get_session_in_plan_and_club(
    db: SASession, club_id: int, plan_id: int, session_id: int
) -> SessionModel:
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
    return session


def insert_session(db: Session, *, plan_id: int, **fields) -> SessionModel:
    session = SessionModel(plan_id=plan_id, **fields)
    db.add(session)
    db.flush()
    return session

def list_sessions(db: SASession, club_id: int, plan_id: int, me) -> list[SessionModel]:
    """List all sessions in a plan within a club."""""

    stmt = (
        sa.select(SessionModel)
        .where(SessionModel.plan_id == plan_id)
        .order_by(SessionModel.starts_at.asc(), SessionModel.id.asc())
    )
    return db.execute(stmt).scalars().all()


def update_session(db: SASession, session, **updates) -> SessionModel:
    for k, v in updates.items():
        setattr(session, k, v)
    db.flush()
    return session

def delete_session(db: SASession, session) -> None:
    db.delete(session)
    db.flush()
