from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.models import Membership, MembershipRole

def assert_can_manage_club(role: MembershipRole) -> None:
    """
    Raise 403 if the caller is not allowed to manage a club.
    Adjust rule as you like (owner-only or owner/coach).
    """
    allowed = {MembershipRole.owner}  # or {MembershipRole.owner, MembershipRole.coach}
    if role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to manage this club")


def assert_is_member_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    """
    Check if the user is a member of the club.
    Raises 403 if not a member.
    Returns the Membership object if a member.
    """
    member = db.execute(
        select(Membership).where(
            # fix Membership.user == user.id to Membership.user == user_id
            Membership.user_id == user_id,
            Membership.club_id == club_id,
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this club"
        )
    return member


def assert_is_coach_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    """
    Check if the user is a coach of the club.
    Raises 403 if not a coach.
    :param db: Session
    :param user_id: user id
    :param club_id: club id
    :return: membership object
    """
    member = db.execute(
        select(Membership).where(
            Membership.user_id == user_id, Membership.club_id == club_id
        )
    ).scalar_one_or_none()
    if not member or member.role != MembershipRole.coach:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coach role required for this club",
        )
    return member


def assert_not_last_coach(db: Session, club_id: int) -> None:
    """
    Check if there is more than one coach in the club.
    Raises 400 if there is only one coach.
    :param db: Session
    :param club_id: club id
    :return: None
    """
    count = db.scalars(
        select(func.count())
        .select_from(Membership)
        .where(
            (Membership.club_id == club_id) & (Membership.role == MembershipRole.coach)
        )
    ).one()
    if count <= 1:
        raise HTTPException(
            status_code=400, detail="Cannot remove the last coach of the club"
        )


def assert_not_last_coach_excluding(
    db: Session, *, club_id: int, excluding_user_id: int
) -> None:
    """
    Check if there is more than one coach in the club, excluding a specific user.
    Raises 400 if there is only one coach left after excluding the specified user.
    :param db: Session
    :param club_id: club id
    :param excluding_user_id: user id to exclude from the count
    :return: None
    """
    remaining = db.scalar(
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.club_id == club_id,
            Membership.role == MembershipRole.coach,
            Membership.user_id != excluding_user_id,  # Ziel ausschließen
        )
    )
    if remaining == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the last coach of the club",
        )
