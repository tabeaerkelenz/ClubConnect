# app/crud/group_membership.py
from sqlalchemy import select, insert, delete, update
from sqlalchemy.orm import Session
from app.db.models import GroupMembership, Group, Membership  # Membership = Club-Mitgliedschaft

def list_group_memberships(db: Session, group_id: int) -> list[GroupMembership]:
    stmt = select(GroupMembership).where(GroupMembership.group_id == group_id).order_by(GroupMembership.user_id.asc())
    return db.execute(stmt).scalars().all()

def get_group_membership(db: Session, group_id: int, user_id: int) -> GroupMembership | None:
    stmt = select(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
    )
    return db.execute(stmt).scalar_one_or_none()

def add_group_member(db: Session, group_id: int, user_id: int, role: str | None) -> GroupMembership:
    existing = get_group_membership(db, group_id, user_id)
    if existing:
        if role is not None:
            existing.role = role
        db.commit(); db.refresh(existing)
        return existing

    gm = GroupMembership(group_id=group_id, user_id=user_id, role=role)
    db.add(gm)
    db.commit(); db.refresh(gm)
    return gm

def remove_group_member(db: Session, group_id: int, user_id: int) -> None:
    stmt = delete(GroupMembership).where(
        GroupMembership.group_id == group_id, GroupMembership.user_id == user_id
    )
    db.execute(stmt); db.commit()
