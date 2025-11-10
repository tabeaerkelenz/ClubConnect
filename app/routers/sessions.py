from typing import List
from sqlalchemy.orm import Session as SASession
from fastapi import APIRouter, Depends, status

from app.db.deps import get_db
from app.schemas.session import SessionRead, SessionCreate, SessionUpdate
from app.auth.deps import get_current_user

from app.services.session import (
    list_sessions_service,
    create_session_service,
    get_session_service,
    update_session_service,
    delete_session_service,
)

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/sessions",
    tags=["sessions"],
)


# ===== Collection =====
@router.get("", response_model=List[SessionRead])
def list_sessions_ep(
    club_id: int,
    plan_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    return list_sessions_service(db, club_id, plan_id, me)


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
    return create_session_service(db, club_id, plan_id, me, data)


# ===== Detail =====
@router.get("/{session_id}", response_model=SessionRead)
def get_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    return get_session_service(db, club_id, plan_id, session_id, me)


@router.patch("/{session_id}", response_model=SessionRead)
def update_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    data: SessionUpdate,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    return update_session_service(db, club_id, plan_id, session_id, me, data)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    db: SASession = Depends(get_db),
    me=Depends(get_current_user),
):
    delete_session_service(db, club_id, plan_id, session_id, me)
