from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from ClubConnect.app.db.models import Membership, MembershipRole, User

def assert_is_member_of_club(db: Session, user: User, club_id: int) -> None:
    m = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.club_id == club_id
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this club")

def assert_is_coach_of_club(db: Session, user: User, club_id: int) -> None:
    m = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.club_id == club_id
        )
    ).scalar_one_or_none()
    if not m or m.role != MembershipRole.coach:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Coach role required for this club")
