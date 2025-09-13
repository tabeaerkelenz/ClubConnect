from typing import NoReturn, List
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from ClubConnect.app.auth.deps import get_current_user
from ClubConnect.app.crud.plan import NotCoachOfClubError, PlanNotFoundError, get_plan, get_plans, delete_plan
from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import User
from ClubConnect.app.schemas.plan import PlanRead, PlanCreate, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])

db_dep = Depends(get_db)
me_dep = Depends(get_current_user)

def _map_crud_errors(exc: Exception) -> NoReturn:
    if isinstance(exc, NotCoachOfClubError):
        raise HTTPException(status_code=403, detail="Not Coach of this Club")
    if isinstance(exc, PlanNotFoundError):
        raise HTTPException(status_code=404, detail="Plan not found")
    raise

@router.get("", response_model=List[PlanRead])
def list_plans(club_id: int, db: Session = db_dep, me: User = me_dep) -> List[PlanRead]:
    plans = get_plans(db, club_id=club_id, me=me)
    return [PlanRead.model_validate(p) for p in plans]


@router.post("", response_model=PlanRead, status_code=201)
def create_plan(club_id: int, data: PlanCreate, db: Session = db_dep, me: User = me_dep)  -> PlanRead:
    try:
        plan = create_plan(db, club_id=club_id, me=me, data=data)
        return PlanCreate.model_validate(plan)
    except Exception as e:
        _map_crud_errors(e)

@router.get("/{plan_id}", response_model=PlanRead)
def get_plan_by_id(club_id: int, plan_id: int, db: Session = db_dep, me: User = me_dep) -> PlanRead:
    plan = get_plan(db, plan_id=plan_id, club_id=club_id, me=me)
    if not plan:
        raise PlanNotFoundError("Plan not found")
    return PlanRead.model_validate(plan)

@router.patch("/{plan_id}", response_model=PlanUpdate)
def update_plan_by_id(plan_id: int, club_id: int, data: PlanRead, db: Session = db_dep, me: User = me_dep) -> PlanRead:
    plan = create_plan(db, club_id=club_id, plan_id=plan_id, me=me, data=data)
    if not plan:
        raise NotCoachOfClubError("Only Coach of Club can update plan")
    return PlanRead.model_validate(plan)

@router.delete("/{plan_id}", status_code=204)
def delete_plan_by_id(club_id: str, plan_id: int, db: Session = db_dep, me: User = me_dep):
    delete_plan(db, club_id=club_id, plan_id=plan_id, me=me)
    return None