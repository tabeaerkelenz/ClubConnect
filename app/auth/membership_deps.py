from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.models import Membership, MembershipRole

def _get_membership(db: Session, user_id: int, club_id: int) -> Membership | None:
    return db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.club_id == club_id,
        )
    ).scalar_one_or_none()

def assert_has_any_role_of_club(
    db: Session,
    user_id: int,
    club_id: int,
    allowed_roles: Iterable[MembershipRole],
    *,
    detail: str = "Insufficient permissions for this club",
) -> Membership:
    """
    Checks for membership returns 403 if not a member of the club.
    """
    member = _get_membership(db, user_id, club_id)
    if not member or member.role not in set(allowed_roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    return member



def assert_is_member_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    return assert_has_any_role_of_club(
        db, user_id, club_id,
        allowed_roles=(MembershipRole.member, MembershipRole.coach, MembershipRole.owner),
        detail="You are not a member of this club",
    )

def assert_is_coach_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    return assert_has_any_role_of_club(
        db, user_id, club_id,
        allowed_roles=(MembershipRole.coach,),   # nur Coach
        detail="Coach role required for this club",
    )

def assert_is_owner_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    return assert_has_any_role_of_club(
        db, user_id, club_id,
        allowed_roles=(MembershipRole.owner,),   # nur Owner
        detail="Owner role required for this club",
    )

def assert_is_coach_or_owner_of_club(db: Session, user_id: int, club_id: int) -> Membership:
    return assert_has_any_role_of_club(
        db, user_id, club_id,
        allowed_roles=(MembershipRole.coach, MembershipRole.owner),  # Coach ODER Owner
        detail="Coach or Owner role required for this club",
    )


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

def count_coach_owner(db, club_id: int, exclude_user_id: int) -> int:
    stmt = (
        select(func.count())
        .select_from(Membership)
        .where(
            Membership.club_id == club_id,
            Membership.role.in_([MembershipRole.coach, MembershipRole.owner]),  # <- include owner
            Membership.user_id != exclude_user_id,
        )
    )
    return db.scalar(stmt) or 0