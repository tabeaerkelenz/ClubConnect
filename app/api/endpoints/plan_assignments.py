from fastapi import APIRouter, Depends, status
from app.auth.deps import get_current_user
from app.schemas.plan_assignment import PlanAssigneeRead, PlanAssigneeCreate
from app.services.plan_assignment import PlanAssignmentService
from app.core.dependencies import get_plan_assignment_service

router = APIRouter(
    prefix="/clubs/{club_id}/plans/{plan_id}/assignees",
    tags=["plan-assignments"],
)

@router.get("", response_model=list[PlanAssigneeRead])
def list_assignees_ep(
    club_id: int,
    plan_id: int,
    service: PlanAssignmentService = Depends(get_plan_assignment_service),
    me=Depends(get_current_user),
):
    return service.list_assignees(club_id=club_id, plan_id=plan_id, me_id=me.id)

@router.post("", response_model=PlanAssigneeRead, status_code=status.HTTP_201_CREATED)
def add_assignee_ep(
    club_id: int,
    plan_id: int,
    data: PlanAssigneeCreate,
    service: PlanAssignmentService = Depends(get_plan_assignment_service),
    me=Depends(get_current_user),
):
    return service.add_assignee(club_id=club_id, plan_id=plan_id, me_id=me.id, data=data)

@router.delete("/{assignee_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_assignee_ep(
    club_id: int,
    plan_id: int,
    assignee_id: int,
    service: PlanAssignmentService = Depends(get_plan_assignment_service),
    me=Depends(get_current_user),
):
    service.remove_assignee(club_id=club_id, plan_id=plan_id, assignee_id=assignee_id, me_id=me.id)
    return None
