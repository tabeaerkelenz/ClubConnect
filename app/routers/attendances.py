from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud.attendance import list_attendances_by_session
from app.db.database import get_db
from app.db.models import User
from app.auth.deps import get_current_user
from app.auth.membership_asserts import assert_is_coach_of_club
from app.schemas.attendance import AttendanceRead, AttendanceCreate, AttendanceUpdate
from app.services.attendance import (
    create_attendance_service,
    list_attendances_service,
    get_attendance_service,
    update_attendance_service,
)

def require_coach_of_club(
    club_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    assert_is_coach_of_club(db, me.id, club_id)

router = APIRouter(
    prefix="/clubs/{club_id}/sessions/{session_id}/attendances",
    tags=["attendances"],
    dependencies=[Depends(require_coach_of_club)],
)

@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_attendance_ep(
    club_id: int,
    session_id: int,
    user_id: int,                    # ?user_id=...
    payload: AttendanceCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    try:
        return create_attendance_service(
            db=db, me_id=me.id, club_id=club_id, session_id=session_id, user_id=user_id, data=payload
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[AttendanceRead], response_model_exclude_none=True)
def list_attendances_ep(
    club_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    return list_attendances_service(db=db, me_id=me.id, club_id=club_id, session_id=session_id, skip=0, limit=50)

@router.get("/{attendance_id}", response_model=AttendanceRead, response_model_exclude_none=True)
def get_attendance_ep(
    club_id: int,
    attendance_id: int,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    return get_attendance_service(db=db, me_id=me.id, club_id=club_id, attendance_id=attendance_id)

@router.patch("/{attendance_id}", response_model=AttendanceRead, response_model_exclude_none=True)
def update_attendance_ep(
    club_id: int,
    attendance_id: int,
    payload: AttendanceUpdate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    return update_attendance_service(db=db, me_id=me.id, club_id=club_id, attendance_id=attendance_id, data=payload)
