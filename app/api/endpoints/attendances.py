from fastapi import APIRouter, Depends, status
from app.auth.deps import get_current_user
from app.schemas.attendance import AttendanceRead, AttendanceCreate, AttendanceUpdate
from app.services.attendance import AttendanceService
from app.core.dependencies import get_attendance_service

router = APIRouter(
    prefix="/clubs/{club_id}/sessions/{session_id}/attendances",
    tags=["attendances"],
)

@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True)
def create_attendance_ep(
    club_id: int,
    session_id: int,
    user_id: int,  # keep as query param for now
    payload: AttendanceCreate,
    service: AttendanceService = Depends(get_attendance_service),
    me=Depends(get_current_user),
):
    return service.create(club_id=club_id, session_id=session_id, user_id=user_id, me_id=me.id, data=payload)

@router.get("", response_model=list[AttendanceRead], response_model_exclude_none=True)
def list_attendances_ep(
    club_id: int,
    session_id: int,
    service: AttendanceService = Depends(get_attendance_service),
    me=Depends(get_current_user),
):
    return service.list_by_session(club_id=club_id, session_id=session_id, me_id=me.id, skip=0, limit=50)

@router.get("/{attendance_id}", response_model=AttendanceRead, response_model_exclude_none=True)
def get_attendance_ep(
    club_id: int,
    session_id: int,  # (optional) keep in path for consistency, service doesn’t need it
    attendance_id: int,
    service: AttendanceService = Depends(get_attendance_service),
    me=Depends(get_current_user),
):
    return service.get(club_id=club_id, attendance_id=attendance_id, me_id=me.id)

@router.patch("/{attendance_id}", response_model=AttendanceRead, response_model_exclude_none=True)
def update_attendance_ep(
    club_id: int,
    session_id: int,
    attendance_id: int,
    payload: AttendanceUpdate,
    service: AttendanceService = Depends(get_attendance_service),
    me=Depends(get_current_user),
):
    return service.update(club_id=club_id, attendance_id=attendance_id, session_id=session_id, me_id=me.id, data=payload)
