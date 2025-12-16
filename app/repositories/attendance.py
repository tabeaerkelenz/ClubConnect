from __future__ import annotations

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Attendance, Session as SessionModel, Plan, AttendanceStatus
from app.schemas.attendance import AttendanceUpdate
from app.exceptions.base import (
    AttendanceNotFoundError,
    AttendanceExistsError,
    SessionNotFound,
)

class AttendanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _session_in_club_exists(self, *, club_id: int, session_id: int) -> bool:
        stmt = (
            select(SessionModel.id)
            .join(Plan, Plan.id == SessionModel.plan_id)
            .where(SessionModel.id == session_id, Plan.club_id == club_id)
        )
        return self.db.execute(stmt).scalar_one_or_none() is not None

    def create(
        self,
        *,
        session_id: int,
        user_id: int,
        status: AttendanceStatus,
        recorded_by_id: int | None,
        checked_in_at: datetime | None,
        checked_out_at: datetime | None,
        note: str | None,
    ) -> Attendance:
        att = Attendance(
            session_id=session_id,
            user_id=user_id,
            status=status,
            recorded_by_id=recorded_by_id,
            checked_in_at=checked_in_at,
            checked_out_at=checked_out_at,
            note=note,
        )
        self.db.add(att)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # Handle uq_attendance_session_user
            raise AttendanceExistsError() from e
        self.db.refresh(att)
        return att

    def list_by_session_in_club(
        self,
        *,
        club_id: int,
        session_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Attendance]:
        if not self._session_in_club_exists(club_id=club_id, session_id=session_id):
            raise SessionNotFound()

        stmt = (
            select(Attendance)
            .where(Attendance.session_id == session_id)
            .order_by(Attendance.id.asc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.execute(stmt).scalars().all()

    def get_in_club(self, *, club_id: int, attendance_id: int) -> Attendance:
        stmt = (
            select(Attendance)
            .join(SessionModel, SessionModel.id == Attendance.session_id)
            .join(Plan, Plan.id == SessionModel.plan_id)
            .where(Attendance.id == attendance_id, Plan.club_id == club_id)
        )
        att = self.db.execute(stmt).scalar_one_or_none()
        if not att:
            raise AttendanceNotFoundError()
        return att

    def update(self, attendance: Attendance, *, data: AttendanceUpdate) -> Attendance:
        changes = data.model_dump(exclude_unset=True)

        # protect immutable fields
        for k in ("id", "created_at", "updated_at", "session_id", "user_id"):
            changes.pop(k, None)

        for field, value in changes.items():
            setattr(attendance, field, value)

        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise AttendanceExistsError() from e
        self.db.refresh(attendance)
        return attendance
