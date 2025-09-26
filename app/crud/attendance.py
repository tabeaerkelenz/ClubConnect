from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Attendance, AttendanceStatus
from app.schemas.attendance import AttendanceUpdate

def create_attendance(
    db: Session,
    *,
    user_id: int,
    session_id: int,
    status: AttendanceStatus | str,
    recorded_by: int | None = None,
    checked_in_at: datetime | None = None,
    checked_out_at: datetime | None = None,
    note: str | None = None,
) -> Attendance:
    att = Attendance(
        user_id=user_id,
        session_id=session_id,
        status=status,
        recorded_by_id=recorded_by,      # FK-Spalte benutzen
        checked_in_at=checked_in_at,
        checked_out_at=checked_out_at,
        note=note,
    )
    db.add(att)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(att)
    return att

def list_attendances_by_session(
    db: Session,
    session_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Attendance]:
    stmt = (
        select(Attendance)
        .where(Attendance.session_id == session_id)
        .order_by(Attendance.id.asc())
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()
def get_attendance(db: Session, attendance_id: int) -> Attendance | None:
    return db.get(Attendance, attendance_id)

def update_attendance(db: Session, attendance: Attendance, data: AttendanceUpdate) -> Attendance:
    changes = data.model_dump(exclude_unset=True)
    for k in ("id", "created_at", "session_id", "user_id"):
        changes.pop(k, None)

    # simple rule
    ci = changes.get("checked_in_at", attendance.checked_in_at)
    co = changes.get("checked_out_at", attendance.checked_out_at)
    if ci and co and co < ci:
        raise ValueError("checked_out_at cannot be before checked_in_at")

    for field, value in changes.items():
        setattr(attendance, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(attendance)
    return attendance
