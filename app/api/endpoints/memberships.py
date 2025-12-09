from typing import List
from fastapi import APIRouter, Depends

from app.auth.deps import get_current_user
from app.core.dependencies import get_membership_service
from app.models.models import User, MembershipRole
from app.schemas.membership import (
    MembershipRead,
    MembershipUpdate,
    MembershipCreate,
)
from app.services.membership import MembershipService

# Club view (list members of a club)
clubs_memberships_router = APIRouter(
    prefix="/clubs/{club_id}/memberships", tags=["memberships"]
)

# current user view (all my memberships across clubs)
memberships_router = APIRouter(prefix="/memberships", tags=["memberships"])


me_dep = Depends(get_current_user)


@clubs_memberships_router.get("", response_model=List[MembershipRead])
def list_club_memberships(
    club_id: int,
    current_user: User = me_dep,
    membership_service: MembershipService = Depends(get_membership_service),
) -> List[MembershipRead]:
    # Ensure current user is at least a member of the club
    membership_service.require_member_of_club(user_id=current_user.id, club_id=club_id)

    rows = membership_service.list_club_memberships(club_id=club_id)
    return [MembershipRead.model_validate(r, from_attributes=True) for r in rows]


@memberships_router.get("/mine", response_model=list[MembershipRead])
def my_memberships(current_user: User = me_dep, membership_service: MembershipService = Depends(get_membership_service)) -> list[MembershipRead]:
    memberships = membership_service.list_user_memberships_by_email(email=current_user.email)
    return [
        MembershipRead.model_validate(membership, from_attributes=True)
        for membership in memberships
    ]


@clubs_memberships_router.post("", response_model=MembershipRead, status_code=201)
def add_membership(
    club_id: int,
    membership_create: MembershipCreate,
    current_user: User = me_dep,
    membership_service: MembershipService = Depends(get_membership_service),
) -> MembershipRead:
    # Ensure current user is at least a coach or owner of the club
    membership_service.require_coach_or_owner_of_club(user_id=current_user.id, club_id=club_id)

    membership = membership_service.add_member_by_email(club_id=club_id, email=membership_create.email, role=membership_create.role)
    return MembershipRead.model_validate(membership, from_attributes=True)


@clubs_memberships_router.post("/join", response_model=MembershipRead, status_code=201)
def self_join(
        club_id: int,
        membership_create: MembershipCreate,
        current_user: User = me_dep,
        membership_service: MembershipService = Depends(get_membership_service),
) -> MembershipRead:
    membership = membership_service.add_member_by_email(
            club_id=club_id, email=current_user.email, role=MembershipRole.member
        )
    return MembershipRead.model_validate(membership, from_attributes=True)


@clubs_memberships_router.patch(
    "/{membership_id:int}/role", response_model=MembershipRead
)
def change_role(
    club_id: int,
    membership_id: int,
    membership_update: MembershipUpdate,
    current_user: User = me_dep,
    membership_service: MembershipService = Depends(get_membership_service)
):
    membership_service.require_coach_or_owner_of_club(user_id=current_user.id, club_id=club_id)
    membership = membership_service.change_role(
            club_id=club_id, membership_id=membership_id, new_role=membership_update.role
        )
    return MembershipRead.model_validate(membership, from_attributes=True)


@clubs_memberships_router.delete("/{membership_id:int}", status_code=204)
def remove_membership(
    club_id: int,
    membership_id: int,
    current_user: User = me_dep,
    membership_service: MembershipService = Depends(get_membership_service),
) -> None:
    # Guard: only coach/owner of this club may remove memberships
    membership_service.require_coach_or_owner_of_club(
        user_id=current_user.id,
        club_id=club_id,
    )

    membership_service.remove_member(
        club_id=club_id,
        membership_id=membership_id,
    )
    return None