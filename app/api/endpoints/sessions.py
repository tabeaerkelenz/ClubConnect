from typing import List

from fastapi import APIRouter, Depends, status, HTTPException

from app.auth.deps import get_current_user
from app.schemas.session import SessionRead, SessionCreate, SessionUpdate
from app.services.session import SessionService
from app.core.dependencies import get_session_service

from app.exceptions.base import (
    PlanNotFoundError,
    SessionNotFound,
    NotClubMember,
    CoachOrOwnerRequiredError,
    InvalidTimeRange,
    ConflictError,
)

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
    try:
        return service.list_sessions(club_id=club_id, plan_id=plan_id, user_id=me.id)
    except NotClubMember as e:
        raise HTTPException(status_code=403, detail=str(e) or "Not a club member")
    except PlanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e) or "Plan not found")


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
def create_session_ep(
    club_id: int,
    plan_id: int,
    data: SessionCreate,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    try:
        return service.create_session(
            club_id=club_id, plan_id=plan_id, user_id=me.id, data=data
        )
    except CoachOrOwnerRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e) or "Coach or owner required")
    except PlanNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e) or "Plan not found")
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e) or "Conflict")


@router.get("/{session_id}", response_model=SessionRead)
def get_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    try:
        return service.get_session(
            club_id=club_id, plan_id=plan_id, session_id=session_id, user_id=me.id
        )
    except NotClubMember as e:
        raise HTTPException(status_code=403, detail=str(e) or "Not a club member")
    except SessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e) or "Session not found")


@router.patch("/{session_id}", response_model=SessionRead)
def update_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    data: SessionUpdate,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    try:
        return service.update_session(
            club_id=club_id,
            plan_id=plan_id,
            session_id=session_id,
            user_id=me.id,
            data=data,
        )
    except CoachOrOwnerRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e) or "Coach or owner required")
    except InvalidTimeRange as e:
        raise HTTPException(status_code=422, detail=str(e) or "Invalid time range")
    except SessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e) or "Session not found")
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e) or "Conflict")


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session_ep(
    club_id: int,
    plan_id: int,
    session_id: int,
    service: SessionService = Depends(get_session_service),
    me=Depends(get_current_user),
):
    try:
        service.delete_session(
            club_id=club_id, plan_id=plan_id, session_id=session_id, user_id=me.id
        )
    except CoachOrOwnerRequiredError as e:
        raise HTTPException(status_code=403, detail=str(e) or "Coach or owner required")
    except SessionNotFound as e:
        raise HTTPException(status_code=404, detail=str(e) or "Session not found")
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e) or "Conflict")
