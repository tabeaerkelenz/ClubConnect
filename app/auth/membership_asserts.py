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

# dont keep this one
def assert_not_last_coach(db: Session, club_id: int) -> None:
    count = db.scalars(
        select(func.count()).select_from(Membership).where(
            (Membership.club_id == club_id) & (Membership.role == MembershipRole.coach)
        )
    ).one()
    if count <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last coach of the club")

# keep this one it also looks if there remains a coach after the actual one gets deleted.
def assert_not_last_coach_excluding(db: Session, *, club_id: int, excluding_user_id: int) -> None:
    remaining = db.scalar(
        select(func.count()).select_from(Membership).where(
            Membership.club_id == club_id,
            Membership.role == MembershipRole.coach,
            Membership.user_id != excluding_user_id,  # Ziel ausschließen
        )
    )
    if remaining == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot remove the last coach of the club")