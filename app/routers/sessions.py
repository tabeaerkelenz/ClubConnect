from typing import List
from sqlalchemy.orm import Session as SASession
from fastapi import APIRouter, Depends, Response, status, HTTPException

from app.schemas.session import SessionRead, SessionCreate, SessionUpdate
from app.crud import session as sessions_crud
from app.auth.membership_asserts import assert_is_member_of_club, assert_is_coach_of_club
from app.auth.deps import get_current_user
from app.db.database import get_db  # or wherever your get_db lives

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/sessions",
    tags=["sessions"],
)


_ERROR_MAP = {
    sessions_crud.NotClubMember:   (status.HTTP_403_FORBIDDEN,  "User is not a member of this club."),
    sessions_crud.NotCoach:        (status.HTTP_403_FORBIDDEN,  "Coach role required for this action."),
    sessions_crud.Conflict:        (status.HTTP_409_CONFLICT,   "Conflict (e.g., unique/constraint)."),
    sessions_crud.InvalidTimeRange:(status.HTTP_422_UNPROCESSABLE_ENTITY, "starts_at must be before ends_at."),
    sessions_crud.SessionNotFound: (status.HTTP_404_NOT_FOUND,  "Session not found."),
}
DOMAIN_ERRORS = tuple(_ERROR_MAP.keys())

def to_http_exc(err: Exception) -> HTTPException:
    # handles subclasses too (future-proof if you refine errors later)
    for cls in err.__class__.__mro__:
        if cls in _ERROR_MAP:
            code, detail = _ERROR_MAP[cls]
            return HTTPException(status_code=code, detail=detail)
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")


# ===== Collection =====
@router.get("", response_model=List[SessionRead])
def list_sessions_ep(
    club_id: int,
    plan_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    # Guards: member can read
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return sessions_crud.list_sessions(db, club_id, plan_id, me)
    except DOMAIN_ERRORS as e:
        raise to_http_exc(e)


@router.post(
    "",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_session_ep(
    club_id: int,
    plan_id: int,
    data: SessionCreate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    # Guards: coach can write
    assert_is_coach_of_club(db, me.id, club_id)
    try:
        return sessions_crud.create_session(db, club_id, plan_id, me, data)
    except DOMAIN_ERRORS as e:
        raise to_http_exc(e)


# ===== Detail =====
@router.get("/{session_id}", response_model=SessionRead)
def get_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    # Guards: member can read
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return sessions_crud.get_session(db, club_id, plan_id, session_id, me)
    except DOMAIN_ERRORS as e:
        raise to_http_exc(e)


@router.patch("/{session_id}", response_model=SessionRead)
def update_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    data: SessionUpdate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    # Guards: coach can write
    assert_is_coach_of_club(db, me.id, club_id)
    try:
        # Router enforces partial updates via exclude_unset in CRUD
        return sessions_crud.update_session(db, club_id, plan_id, session_id, me, data)
    except DOMAIN_ERRORS as e:
        raise to_http_exc(e)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    # Guards: coach can write
    assert_is_coach_of_club(db, me.id, club_id)
    try:
        sessions_crud.delete_session(db, club_id, plan_id, session_id, me)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except DOMAIN_ERRORS as e:
        raise to_http_exc(e)
