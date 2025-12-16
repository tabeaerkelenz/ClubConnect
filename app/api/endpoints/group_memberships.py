from fastapi import APIRouter, Depends, status

from app.schemas.group_membership import (
    GroupMembershipCreate,
    GroupMembershipRead,
    GroupMembershipSet,
)
from app.services.group_membership import GroupMembershipService
from app.core.dependencies import get_group_membership_service

from app.auth.deps import get_current_user


router = APIRouter(
    prefix="/clubs/{club_id}/groups/{group_id}/memberships",
    tags=["Group Memberships"],
)


@router.get(
    "",
    response_model=list[GroupMembershipRead],
)
def list_group_memberships(
    club_id: int,
    group_id: int,
    gm_service: GroupMembershipService = Depends(get_group_membership_service),
    me=Depends(get_current_user),
):
    return gm_service.list_members(actor_id=me.id, club_id=club_id, group_id=group_id)


@router.post(
    "",
    response_model=GroupMembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def add_group_member(
    club_id: int,
    group_id: int,
    group_member_create: GroupMembershipCreate,
    gm_service: GroupMembershipService = Depends(get_group_membership_service),
    me=Depends(get_current_user),
):
    return gm_service.add_member(
        actor_id=me.id,
        club_id=club_id,
        group_id=group_id,
        user_id=group_member_create.user_id,
        role=group_member_create.role,
    )


@router.put(
    "/{user_id}",
    response_model=GroupMembershipRead,
)
def set_group_member_role(
    club_id: int,
    group_id: int,
    user_id: int,
    group_member_set: GroupMembershipSet,
    gm_service: GroupMembershipService = Depends(get_group_membership_service),
    me=Depends(get_current_user),
):
    return gm_service.set_member_role(
        actor_id=me.id,
        club_id=club_id,
        group_id=group_id,
        user_id=user_id,
        role=group_member_set.role,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_group_member(
    club_id: int,
    group_id: int,
    user_id: int,
    gm_service: GroupMembershipService = Depends(get_group_membership_service),
    me=Depends(get_current_user),
):
    gm_service.remove_member(actor_id=me.id, club_id=club_id, group_id=group_id, user_id=user_id)
    return None
