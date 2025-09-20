from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.auth.deps import get_current_user
from app.auth.membership_asserts import assert_is_member_of_club, assert_is_coach_of_club
from app.schemas.plan_assignment import PlanAssigneeRead, PlanAssigneeCreate
from app.services import *

from ClubConnect.app.services.plan_assignment import list_assignees_service, add_assignee_service, \
    remove_assignee_service

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/assignees",
    tags=["plan-assignments"],
)

def _map_error(e: Exception) -> None:
    name = e.__class__.__name__
    if name in {"PlanNotFound", "PlanAssigneeNotFound"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    if name in {"UserNotClubMember"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if name in {"Conflict"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    raise e

@router.get("", response_model=list[PlanAssigneeRead])
def list_assignees_ep(club_id: int, plan_id: int,
                      db: Session = Depends(get_db),
                      me=Depends(get_current_user)):
    assert_is_member_of_club(db, me.id, club_id)
    try:
        return list_assignees_service(db, club_id, plan_id, me)
    except Exception as e:
        _map_error(e)

@router.post("", response_model=PlanAssigneeRead, status_code=status.HTTP_201_CREATED)
def add_assignee_ep(club_id: int, plan_id: int, data: PlanAssigneeCreate,
                    db: Session = Depends(get_db),
                    me=Depends(get_current_user)):
    assert_is_coach_of_club(db, me.id, club_id)
    try:
        return add_assignee_service(db, club_id, plan_id, me, data)
    except Exception as e:
        _map_error(e)

@router.delete("/{assignee_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignee_ep(club_id: int, plan_id: int, assignee_id: int,
                       db: Session = Depends(get_db),
                       me=Depends(get_current_user)):
    assert_is_coach_of_club(db, me.id, club_id)
    try:
        remove_assignee_service(db, club_id, plan_id, assignee_id, me)
    except Exception as e:
        _map_error(e)
