from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Session as SessionModel, Plan
from app.exceptions.base import (
    PlanNotFoundError,
    SessionNotFound,
    ConflictError,
)


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- helpers ----------

    def _get_plan_in_club(self, *, club_id: int, plan_id: int) -> Plan:
        stmt = sa.select(Plan).where(
            Plan.id == plan_id,
            Plan.club_id == club_id,
        )
        plan = self.db.execute(stmt).scalar_one_or_none()
        if not plan:
            raise PlanNotFoundError()
        return plan

    def _get_session_in_plan(
        self, *, club_id: int, plan_id: int, session_id: int
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
        session = self.db.execute(stmt).scalar_one_or_none()
        if not session:
            raise SessionNotFound()
        return session

    # ---------- public API ----------

    def list_in_plan(self, *, club_id: int, plan_id: int) -> list[SessionModel]:
        # strict: plan must exist in club
        self._get_plan_in_club(club_id=club_id, plan_id=plan_id)

        stmt = (
            sa.select(SessionModel)
            .where(SessionModel.plan_id == plan_id)
            .order_by(SessionModel.starts_at.asc(), SessionModel.id.asc())
        )
        return self.db.execute(stmt).scalars().all()

    def get_in_plan(
        self, *, club_id: int, plan_id: int, session_id: int
    ) -> SessionModel:
        return self._get_session_in_plan(
            club_id=club_id, plan_id=plan_id, session_id=session_id
        )

    def create_in_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        created_by_id: int,
        name: str,
        description: str | None,
        starts_at,
        ends_at,
        location: str,
        note: str | None,
    ) -> SessionModel:
        self._get_plan_in_club(club_id=club_id, plan_id=plan_id)

        session = SessionModel(
            plan_id=plan_id,
            created_by=created_by_id,
            name=name,
            description=description,
            starts_at=starts_at,
            ends_at=ends_at,
            location=location,
            note=note,
        )

        try:
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError() from e

    def update_in_plan(
        self,
        *,
        club_id: int,
        plan_id: int,
        session_id: int,
        updates: dict,
    ) -> SessionModel:
        session = self._get_session_in_plan(
            club_id=club_id, plan_id=plan_id, session_id=session_id
        )

        for key, value in updates.items():
            setattr(session, key, value)

        try:
            self.db.commit()
            self.db.refresh(session)
            return session
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError() from e

    def delete_in_plan(
        self, *, club_id: int, plan_id: int, session_id: int
    ) -> None:
        session = self._get_session_in_plan(
            club_id=club_id, plan_id=plan_id, session_id=session_id
        )

        try:
            self.db.delete(session)
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError() from e
