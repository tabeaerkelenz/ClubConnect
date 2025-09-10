from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ClubConnect.app.db.models import Membership, MembershipRole, User

def assert_is_member_of_club(db: Session, user: User, club_id: int) -> Membership:
    member = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.club_id == club_id
        )
    ).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this club")
    return member

def assert_is_coach_of_club(db: Session, user: User, club_id: int) -> Membership:
    member = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.club_id == club_id
        )
    ).scalar_one_or_none()
    if not member or member.role != MembershipRole.coach:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach role required for this club")
    return member


def assert_not_last_coach(db: Session, club_id: int) -> None:
    count = db.scalars(
        select(func.count()).select_from(Membership).where(
            (Membership.club_id == club_id) & (Membership.role == MembershipRole.coach)
        )
    ).one()
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last coach of the club")