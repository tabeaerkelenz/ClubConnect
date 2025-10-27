from typing import NoReturn, List, Literal
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.auth.membership_deps import (
    assert_is_member_of_club,
    assert_is_coach_of_club,
)
from app.db.deps import get_db
from app.services.plan import *
from app.db.models import User, PlanAssigneeRole
from app.schemas.plan import PlanRead, PlanCreate, PlanUpdate

from app.services.plan import (
    list_assigned_plans_service,
    create_plan_service,
    get_plan_service,
    update_plan_service,
    delete_plan_service,
)

router = APIRouter(prefix="/clubs/{club_id}/plans", tags=["plans"])

db_dep = Depends(get_db)
me_dep = Depends(get_current_user)


def _map_crud_errors(exc: Exception) -> NoReturn:
    if isinstance(exc, NotCoachOfClubError):
        raise HTTPException(status_code=403, detail="Not Coach of this Club")
    if isinstance(exc, PlanNotFoundError):
        raise HTTPException(status_code=404, detail="Plan not found")
    raise


@router.get("", response_model=List[PlanRead])
def list_plans_ep(
    club_id: int, db: Session = db_dep, me: User = me_dep
) -> List[PlanRead]:
    assert_is_member_of_club(db, me.id, club_id)
    plans = get_plans_service(db, club_id=club_id, me=me)
    return [PlanRead.model_validate(p) for p in plans]


@router.get("/mine", response_model=list[PlanRead])
def list_assigned_plans_ep(
    club_id: int,
    role: Literal["coach", "athlete"] | None = Query(None),  # optional filter
    db: Session = Depends(get_db),
    me=Depends(get_current_user),
):
    assert_is_member_of_club(db, me.id, club_id)
    return list_assigned_plans_service(db, club_id, me, role=role)


@router.post("", response_model=PlanRead, status_code=201)
# append the function names with ep to avoid shadowing
def create_plan_ep(
    club_id: int, data: PlanCreate, db: Session = db_dep, me: User = me_dep
) -> PlanRead:
    assert_is_member_of_club(db, me.id, club_id)
    try:
        plan = create_plan_service(db, club_id=club_id, me=me, data=data)
        return PlanRead.model_validate(plan)
    except Exception as e:
        _map_crud_errors(e)


@router.get("/{plan_id}", response_model=PlanRead)
def get_plan_by_id_ep(
    club_id: int, plan_id: int, db: Session = db_dep, me: User = me_dep
) -> PlanRead:
    try:
        plan = get_plan_service(db, plan_id=plan_id, club_id=club_id, me=me)
        if not plan:
            raise PlanNotFoundError()
    except Exception as e:
        _map_crud_errors(e)
    return PlanRead.model_validate(plan)


@router.patch("/{plan_id}", response_model=PlanRead)
def update_plan_by_id_ep(
    plan_id: int,
    club_id: int,
    data: PlanUpdate,
    db: Session = db_dep,
    me: User = me_dep,
) -> PlanRead:
    assert_is_member_of_club(db, me.id, club_id)
    # fix update_plan instead of create_plan
    plan = update_plan_service(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
    if not plan:
        raise NotCoachOfClubError("Only Coach of Club can update plan")
    return PlanRead.model_validate(plan)


@router.delete("/{plan_id}", status_code=204)
def delete_plan_by_id_ep(
    club_id: str, plan_id: int, db: Session = db_dep, me: User = me_dep
):
    delete_plan_service(db, club_id=club_id, plan_id=plan_id, me=me)
    return None
