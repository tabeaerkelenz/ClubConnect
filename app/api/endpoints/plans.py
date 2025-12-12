from typing import List, Literal

from fastapi import APIRouter, Depends, Query

from app.auth.deps import get_current_user
from app.models.models import User
from app.schemas.plan import PlanRead, PlanCreate, PlanUpdate
from app.services.plan import PlanService
from app.core.dependencies import get_plan_service

router = APIRouter(prefix="/clubs/{club_id}/plans", tags=["plans"])

me_dep = Depends(get_current_user)
plan_service_dep = Depends(get_plan_service)


@router.get("", response_model=List[PlanRead])
def list_plans_ep(
    club_id: int,
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
) -> List[PlanRead]:
    plans = plan_service.list_plans_for_club(club_id=club_id, me=me)
    return [PlanRead.model_validate(p) for p in plans]


@router.get("/mine", response_model=list[PlanRead])
def list_assigned_plans_ep(
    club_id: int,
    role: Literal["coach", "athlete"] | None = Query(None),
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
):
    plans = plan_service.list_assigned_plans(club_id=club_id, me=me, role=role)
    return [PlanRead.model_validate(p) for p in plans]


@router.post("", response_model=PlanRead, status_code=201)
def create_plan_ep(
    club_id: int,
    data: PlanCreate,
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
) -> PlanRead:
    plan = plan_service.create_plan(club_id=club_id, me=me, data=data)
    return PlanRead.model_validate(plan)


@router.get("/{plan_id}", response_model=PlanRead)
def get_plan_by_id_ep(
    club_id: int,
    plan_id: int,
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
) -> PlanRead:
    plan = plan_service.get_plan(club_id=club_id, plan_id=plan_id, me=me)
    return PlanRead.model_validate(plan)


@router.patch("/{plan_id}", response_model=PlanRead)
def update_plan_by_id_ep(
    club_id: int,
    plan_id: int,
    data: PlanUpdate,
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
) -> PlanRead:
    plan = plan_service.update_plan(
        club_id=club_id, plan_id=plan_id, me=me, data=data
    )
    return PlanRead.model_validate(plan)


@router.delete("/{plan_id}", status_code=204)
def delete_plan_by_id_ep(
    club_id: int,
    plan_id: int,
    me: User = me_dep,
    plan_service: PlanService = plan_service_dep,
):
    plan_service.delete_plan(club_id=club_id, plan_id=plan_id, me=me)
    return None
