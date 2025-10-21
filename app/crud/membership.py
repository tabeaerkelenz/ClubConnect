from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import Membership, MembershipRole


def get_membership_by_id(db, membership_id):
    """Get membership by its ID."""
    return db.get(Membership, membership_id)


def count_other_coaches(db, club_id, user_id):
    """Count the number of coaches in a club excluding a specific user."""
    stmt = (
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.club_id == club_id,
            Membership.role == MembershipRole.coach,
            Membership.user_id != user_id,
        )
    )
    return db.scalar(stmt)


def create_membership(
    db: Session, club_id: int, user_id: int, role: MembershipRole
) -> Membership:
    """Create a new membership."""
    membership = Membership(club_id=club_id, user_id=user_id, role=role)
    db.add(membership)
    return membership


def get_membership(db: Session, *, club_id: int, user_id: int) -> Membership | None:
    """Get a membership by club ID and user ID."""
    stmt = select(Membership).where(
        Membership.club_id == club_id,
        Membership.user_id == user_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def get_memberships_user(db: Session, user_id: int) -> list[Membership]:
    """Get all memberships for a specific user."""
    stmt = select(Membership).where(Membership.user_id == user_id)
    return db.execute(stmt).scalars().all()


def get_memberships_club(db: Session, club_id: int) -> Membership:
    """Get all memberships for a specific club."""
    stmt = select(Membership).where(Membership.club_id == club_id)
    return db.execute(stmt).scalars().all()


def delete_membership(db: Session, club_id: int, membership_id: int) -> None:
    """Delete a membership by its ID."""
    membership = db.get(Membership, membership_id)
    db.delete(membership)
    db.commit()


def update_membership_role(
    db: Session, *, club_id: int, membership_id: int, new_role: MembershipRole
) -> Membership:
    """Update the role of a membership."""
    membership = db.get(Membership, membership_id)
    membership.role = new_role
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership
