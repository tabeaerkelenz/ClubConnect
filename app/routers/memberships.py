from typing import NoReturn, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ClubConnect.app.auth.deps import get_current_user
from ClubConnect.app.db.database import get_db
from ClubConnect.app.db.models import User, MembershipRole, Membership
from ClubConnect.app.schemas.membership import MembershipRead, MembershipCreate, MembershipUpdate, MembershipCreate
from ClubConnect.app.crud.membership import create_membership, get_memberships_club, update_membership_role, delete_membership, UserNotFoundError, MembershipNotFoundError, MembershipExistsError, LastCoachViolationError
from ClubConnect.app.auth.membership_asserts import assert_not_last_coach_excluding, assert_is_coach_of_club, assert_is_member_of_club

router = APIRouter(prefix="/memberships", tags=["memberships"])

db_dep = Depends(get_db)
me_dep = Depends(get_current_user)

def _map_crud_errors(exc: Exception) -> NoReturn:
    if isinstance(exc, UserNotFoundError):
        raise HTTPException(404, "User with that email not found")
    if isinstance(exc, MembershipExistsError):
        raise HTTPException(409, "Membership already exists")
    if isinstance(exc, MembershipNotFoundError):
        raise HTTPException(404, "Membership not found for this club")
    if isinstance(exc, LastCoachViolationError):
        raise HTTPException(400, "Cannot remove the last coach of the club")
    raise

@router.get("", response_model=List[MembershipRead])
def list_memberships(club_id: int, db: Session = db_dep, me: User = me_dep) -> List[MembershipRead]:
    assert_is_member_of_club(db, user=me, club_id=club_id)
    rows = get_memberships_club(db=db, club_id=club_id)
    return [MembershipRead.model_validate(r) for r in rows]

@router.post("", response_model=MembershipRead, status_code=201)
def add_membership(club_id: int, payload: MembershipCreate, db: Session = db_dep, me: User = me_dep) -> MembershipRead:
    assert_is_coach_of_club(db, user=me, club_id=club_id)
    try:
        membership = create_membership(db, club_id=club_id, email=payload.email, role=payload.role)
    except Exception as e:
        _map_crud_errors(e)
    return MembershipRead.model_validate(membership)

@router.post("/join", response_model=MembershipRead, status_code=201)
def self_join(club_id: int, db: Session = db_dep, me: User = me_dep) -> MembershipRead:
    try:
        membership = create_membership(db, club_id=club_id, email=me.email, role=MembershipRole.member)
    except Exception as e:
        _map_crud_errors(e)
    return MembershipRead.model_validate(membership)

@router.patch("/{membership_id:int}/role", response_model=MembershipRead)
def change_role(club_id: int, membership_id: int, payload: MembershipUpdate, db: Session = db_dep, me: User = me_dep):
    assert_is_coach_of_club(db, user=me, club_id=club_id)
    try:
        membership = update_membership_role(db, club_id=club_id, membership_id=membership_id)
    except Exception as e:
        _map_crud_errors(e)
    return MembershipRead.model_validate(membership)

@router.delete("/{membership_id:int}", status_code=204)
def remove_membership(club_id: int, membership_id: int, db: Session = db_dep, me: User = me_dep):
    # load target to decide permission
    target = db.get(Membership, membership_id)
    if not target or target.club_id != club_id:
        raise HTTPException(404, "Membership not found for this club")

    if target.user_id != me.id:
        assert_is_coach_of_club(db, user=me, club_id=club_id)

    try:
        delete_membership(db, membership_id=membership_id)
    except Exception as e:
        _map_crud_errors(e)

    return None

