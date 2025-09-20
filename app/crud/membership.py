from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.crud.club import get_club
from app.crud.user import get_user_by_email
from app.db.models import Membership, MembershipRole

class UserNotFoundError(Exception):
    """No user with the given email exists."""
    pass

class MembershipExistsError(Exception):
    """A membership for (club_id, user_id) already exists."""
    pass

class ClubNotFoundError(Exception):
    """No club with the given id exists."""
    pass

class MembershipNotFoundError(Exception):
    """No membership with the given id exists."""
    pass

class LastCoachViolationError(Exception):
    """No last coach violation with the given id exists."""
    pass


def create_membership(db: Session, *, club_id: int, email: str, role: MembershipRole) -> Membership:
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()

    membership = Membership(club_id=club_id, user_id=user.id, role=role)
    db.add(membership)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise MembershipExistsError() from e

    db.refresh(membership)
    return membership

def get_membership(db: Session, *, club_id: int, user_id: int) -> Membership | None:
    stmt = select(Membership).where(
        Membership.club_id == club_id,
        Membership.user_id == user_id,
    )
    return db.execute(stmt).scalar_one_or_none()

def get_memberships_user(db: Session, email: str) -> list[Membership]:
    user = get_user_by_email(db, email.strip().lower())
    if not user:
        raise UserNotFoundError()
    stmt = select(Membership).where(Membership.user_id == user.id)
    return db.execute(stmt).scalars().all()

def get_memberships_club(db: Session, club_id: int) -> Membership:
    club = get_club(db, club_id)
    if not club:
        raise ClubNotFoundError()
    stmt = select(Membership).where(Membership.club_id == club.id)
    return db.execute(stmt).scalars().all()

def delete_membership(db: Session, *, club_id: int, membership_id: int) -> None:
    membership = db.get(Membership, membership_id)
    if not membership or membership.club_id != club_id:
        raise MembershipNotFoundError()

    if membership.role == MembershipRole.coach:
        remaining = db.scalar(
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.club_id == club_id,
                Membership.role == MembershipRole.coach,
                Membership.user_id != membership.user_id
            )
        )
        if remaining == 0:
            raise LastCoachViolationError()

    db.delete(membership)
    db.commit()

def update_membership_role(
    db: Session, *, club_id: int, membership_id: int, new_role: MembershipRole
) -> Membership:
    membership = db.get(Membership, membership_id)
    if not membership or membership.club_id != club_id:
        raise MembershipNotFoundError()

    # Only guard if demoting a coach
    if membership.role == MembershipRole.coach and new_role != MembershipRole.coach:
        remaining = db.scalar(
            select(func.count()).select_from(Membership).where(
                Membership.club_id == club_id,
                Membership.role == MembershipRole.coach,
                Membership.user_id != membership.user_id,  # exclude the target
            )
        )
        if remaining == 0:
            raise LastCoachViolationError()

    if membership.role == new_role:  # idempotent no-op
        return membership

    membership.role = new_role
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership