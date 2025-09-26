from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.crud.session import get_session_club_id
from app.db.models import Session as SessionModel, Plan
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from app.crud.attendance import (
    create_attendance as crud_create_attendance,
    list_attendances_by_session as crud_list_attendances,
    get_attendance as crud_get_attendance,
    update_attendance as crud_update_attendance,
)
from app.auth.membership_asserts import assert_is_coach_of_club, assert_is_member_of_club

def _assert_session_in_club(db: Session, session_id: int, club_id: int) -> None:
    sess_club_id = get_session_club_id(db, session_id)   # ← nur Repository-Aufruf
    if sess_club_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if sess_club_id != club_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session not in this club")

def create_attendance_service(
    db: Session, *, me_id: int, club_id: int, session_id: int, user_id: int, data: AttendanceCreate
):
    assert_is_coach_of_club(db, me_id, club_id)
    _assert_session_in_club(db, session_id, club_id)
    assert_is_member_of_club(db, user_id, club_id)
    return crud_create_attendance(
        db,
        user_id=user_id,
        session_id=session_id,
        status=data.status or "planned",
        recorded_by=me_id,
        checked_in_at=data.checked_in_at,
        checked_out_at=data.checked_out_at,
        note=data.note,
    )

def list_attendances_service(db: Session, *, me_id: int, club_id: int, session_id: int, skip: int = 0, limit: int = 50):
    assert_is_coach_of_club(db, me_id, club_id)
    # TODO: Falls nötig, hier nach club filtern (JOIN Attendance -> Session -> club_id)
    return crud_list_attendances(db, session_id, skip, limit)

def get_attendance_service(db: Session, *, me_id: int, club_id: int, attendance_id: int):
    assert_is_coach_of_club(db, me_id, club_id)
    att = crud_get_attendance(db, attendance_id)
    if not att:
        raise HTTPException(status_code=404, detail="Attendance not found")
    _assert_session_in_club(db, att.session_id, club_id)
    return att

def update_attendance_service(db: Session, *, me_id: int, club_id: int, attendance_id: int, data: AttendanceUpdate):
    att = get_attendance_service(db, me_id=me_id, club_id=club_id, attendance_id=attendance_id)
    try:
        return crud_update_attendance(db, att, data)
    except Exception:
        db.rollback()
        raise
