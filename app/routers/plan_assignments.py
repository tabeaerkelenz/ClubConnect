from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user

from app.db.deps import get_db
from app.schemas.plan_assignment import PlanAssigneeRead, PlanAssigneeCreate

from app.services.plan_assignment import (
    list_assignees_service,
    add_assignee_service,
    remove_assignee_service,
)

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/assignees",
    tags=["plan-assignments"],
)



@router.get("", response_model=list[PlanAssigneeRead])
def list_assignees_ep(
    club_id: int,
    plan_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    return list_assignees_service(db, club_id, plan_id, me)



@router.post("", response_model=PlanAssigneeRead, status_code=status.HTTP_201_CREATED)
def add_assignee_ep(
    club_id: int,
    plan_id: int,
    data: PlanAssigneeCreate,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    return add_assignee_service(db, club_id, plan_id, me, data)



@router.delete("/{assignee_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignee_ep(
    club_id: int,
    plan_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    remove_assignee_service(db, club_id, plan_id, assignee_id, me)

