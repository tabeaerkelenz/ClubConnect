# app/routers/group_memberships.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import User
from app.auth.deps import get_current_user
from app.schemas.group_membership import GroupMembershipRead, GroupMembershipCreate, GroupMembershipSet, \
    GroupMembershipInvite
from app.services.group_membership import (
    list_group_memberships_service,
    add_group_member_service,
    remove_group_member_service, invite_group_member_service,
)

router = APIRouter(prefix="/clubs/{club_id}/groups/{group_id}/memberships", tags=["group_memberships"])

@router.get("", response_model=list[GroupMembershipRead], response_model_exclude_none=True)
def list_group_members_ep(club_id: int, group_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    return list_group_memberships_service(db, me.id, club_id, group_id)


@router.post("", response_model=GroupMembershipRead, status_code=status.HTTP_201_CREATED)
def add_group_member_ep(
    club_id: int,
    group_id: int,
    payload: GroupMembershipCreate,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Add a user to the group by user ID."""
    return add_group_member_service(db, me.id, club_id, group_id, payload.user_id, payload.role)


@router.post(
    "/invite",
    response_model=GroupMembershipRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_group_member_ep(
    club_id: int,
    group_id: int,
    payload: GroupMembershipInvite,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    """Invite a user by email to join the group."""
    return invite_group_member_service(
        db=db,
        me_id=me.id,
        club_id=club_id,
        group_id=group_id,
        email=payload.email,
        role=payload.role,
    )


@router.put("/{user_id}", response_model=GroupMembershipRead)
def set_group_member_ep(
    club_id: int,
    group_id: int,
    user_id: int,
    payload: GroupMembershipSet,
    db: Session = Depends(get_db),
    me: User = Depends(get_current_user),
):
    return add_group_member_service(db, me.id, club_id, group_id, user_id, payload.role)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_group_member_ep(club_id: int, group_id: int, user_id: int, db: Session = Depends(get_db), me: User = Depends(get_current_user)):
    remove_group_member_service(db, me.id, club_id, group_id, user_id)
    return {"ok": True}
