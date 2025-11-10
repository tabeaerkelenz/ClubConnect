from typing import NoReturn, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.deps import get_db
from app.db.models import User, MembershipRole, Membership
from app.exceptions.base import UserNotFoundError
from app.schemas.membership import (
    MembershipRead,
    MembershipUpdate,
    MembershipCreate,
)
from app.services.membership import (
    create_membership_service,
    get_memberships_club_service,
    update_membership_role_service,
    delete_membership_service,
    get_memberships_user_service,

)
from app.auth.membership_deps import (assert_is_member_of_club, assert_is_coach_or_owner_of_club)

# Club view (list members of a club)
clubs_memberships_router = APIRouter(
    prefix="/clubs/{club_id}/memberships", tags=["memberships"]
)

# My view (all my memberships across clubs)
memberships_router = APIRouter(prefix="/memberships", tags=["memberships"])

db_dep = Depends(get_db)
me_dep = Depends(get_current_user)


@clubs_memberships_router.get("", response_model=List[MembershipRead])
def list_memberships(
    club_id: int,
    db: Session = db_dep,
    me: User = me_dep,
    skip: int = 0,
    limit: int = 50,
) -> List[MembershipRead]:
    assert_is_member_of_club(db, user_id=me.id, club_id=club_id)
    rows = get_memberships_club_service(db=db, club_id=club_id)
    return [MembershipRead.model_validate(r, from_attributes=True) for r in rows]


@memberships_router.get("/mine", response_model=list[MembershipRead])
def my_memberships(db: Session = db_dep, me=me_dep) -> list[MembershipRead]:
    memberships = get_memberships_user_service(db=db, email=me.email)
    return [
        MembershipRead.model_validate(membership, from_attributes=True)
        for membership in memberships
    ]


@clubs_memberships_router.post("", response_model=MembershipRead, status_code=201)
def add_membership(
    club_id: int, payload: MembershipCreate, db: Session = db_dep, me: User = me_dep
) -> MembershipRead:
    membership = create_membership_service(db, club_id=club_id, email=payload.email, role=payload.role)
    return MembershipRead.model_validate(membership, from_attributes=True)


@clubs_memberships_router.post("/join", response_model=MembershipRead, status_code=201)
def self_join(club_id: int, db: Session = db_dep, me: User = me_dep) -> MembershipRead:
    membership = create_membership_service(
            db, club_id=club_id, email=me.email, role=MembershipRole.member
        )
    return MembershipRead.model_validate(membership)


@clubs_memberships_router.patch(
    "/{membership_id:int}/role", response_model=MembershipRead
)
def change_role(
    club_id: int,
    membership_id: int,
    payload: MembershipUpdate,
    db: Session = db_dep,
    me: User = me_dep,
):
    assert_is_coach_or_owner_of_club(db, user_id=me.id, club_id=club_id)
    membership = update_membership_role_service(
            db, club_id=club_id, membership_id=membership_id, new_role=payload.role
        )
    return MembershipRead.model_validate(membership)


@clubs_memberships_router.delete("/{membership_id:int}", status_code=204)
def remove_membership(
    club_id: int, membership_id: int, db: Session = db_dep, me: User = me_dep
):
    delete_membership_service(db, club_id=club_id, membership_id=membership_id)
    return None
