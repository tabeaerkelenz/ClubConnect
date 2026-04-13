from typing import List

from fastapi import APIRouter, Depends, status

from app.auth.deps import get_current_user
from app.schemas.session import SessionRead, SessionCreate, SessionUpdate
from app.services.session import SessionService
from app.core.dependencies import get_session_service

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/sessions",
    tags=["sessions"],
)


@router.get("", response_model=List[SessionRead])
def list_sessions_ep(
    club_id: int,
    plan_id: int,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    return service.list_sessions(club_id=club_id, plan_id=plan_id, user_id=me.id)


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session_ep(
    club_id: int,
    plan_id: int,
    data: SessionCreate,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    return service.create_session(
        club_id=club_id, plan_id=plan_id, user_id=me.id, data=data
    )


@router.get("/{session_id}", response_model=SessionRead)
def get_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    return service.get_session(
        club_id=club_id, plan_id=plan_id, session_id=session_id, user_id=me.id
    )


@router.patch("/{session_id}", response_model=SessionRead)
def update_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    data: SessionUpdate,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    return service.update_session(
        club_id=club_id,
        plan_id=plan_id,
        session_id=session_id,
        user_id=me.id,
        data=data,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    service.delete_session(
        club_id=club_id, plan_id=plan_id, session_id=session_id, user_id=me.id
    )
