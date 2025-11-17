from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import Group
from app.repositories.user import get_user_by_email
from app.repositories.group_membership import (
    list_group_memberships, add_group_member, remove_group_member
)
from app.auth.membership_deps import assert_is_coach_of_club, assert_is_member_of_club

def _ensure_group_in_club(db: Session, group_id: int, club_id: int):
    grp = db.execute(select(Group.club_id).where(Group.id == group_id)).scalar_one_or_none()
    if grp is None:
        raise HTTPException(404, "Group not found")
    if grp != club_id:
        raise HTTPException(403, "Group not in this club")

def list_group_memberships_service(db: Session, me_id: int, club_id: int, group_id: int):
    assert_is_member_of_club(db, me_id, club_id)
    _ensure_group_in_club(db, group_id, club_id)
    return list_group_memberships(db, group_id)

def add_group_member_service(db: Session, me_id: int, club_id: int, group_id: int, user_id: int, role: str | None):
    assert_is_coach_of_club(db, me_id, club_id)
    _ensure_group_in_club(db, group_id, club_id)
    assert_is_member_of_club(db, user_id, club_id)
    try:
        return add_group_member(db, group_id, user_id, role)
    except Exception:
        db.rollback()
        raise


def invite_group_member_service(db: Session, me_id: int, club_id: int, group_id: int, email: str, role: str | None):
    assert_is_coach_of_club(db, me_id, club_id)
    _ensure_group_in_club(db, group_id, club_id)

    user = get_user_by_email(db, email)
    if not user:
        # choose behavior:
        # 1) 404 (simple)
        raise HTTPException(status_code=404, detail="User with this email not found")
        # 2) Or: create pending invite record

    assert_is_member_of_club(db, user.id, club_id)  # or auto-add to club if that’s your policy
    return add_group_member(db, group_id=group_id, user_id=user.id, role=role)


def remove_group_member_service(db: Session, me_id: int, club_id: int, group_id: int, user_id: int):
    assert_is_coach_of_club(db, me_id, club_id)
    _ensure_group_in_club(db, group_id, club_id)
    try:
        remove_group_member(db, group_id, user_id)
    except Exception:
        db.rollback()
        raise
