from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.auth.membership_deps import assert_is_coach_of_club, assert_is_owner_of_club
from app.crud import club as crud
from app.crud.club import get_clubs_by_user, create_club, add_membership
from app.crud.membership import get_membership
from app.db.models import MembershipRole
from app.schemas.club import ClubUpdate


def create_club_service(db, payload, user):
    try:
        club = create_club(db, name=payload.name,
            country=payload.country,
            city=payload.city,
            sport=payload.sport,
            founded_year=payload.founded_year,
            description=payload.description
        )
        add_membership(db, user.id, club.id, MembershipRole.owner)
        db.commit()
        db.refresh(club)
        return club
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Club name already exists")


def get_club_service(db, club_id: int):
    club = crud.get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    return club


def list_clubs_service(db, skip: int = 0, limit: int = 50, q: str | None = None):
    skip = max(0, skip)
    limit = max(1, min(limit, 200))
    return crud.list_clubs(db, skip, limit, q)


def get_my_clubs_service(db, user):
    return get_clubs_by_user(db, user.id)


def update_club_service(db, user, club_id: int, data: ClubUpdate):
    membership = get_membership(db, club_id=club_id, user_id=user.id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    assert_is_owner_of_club(db, user_id=user.id, club_id=club_id)  # raises 403 if not

    club = crud.get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    try:
        return crud.update_club(db, club, data.name)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Club name already exists")


def delete_club_service(db, user, club_id: int):
    membership = get_membership(db, club_id=club_id, user_id=user.id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    assert_is_owner_of_club(db, user.id, club_id)  # raises 403 if not
    club = crud.get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    crud.delete_club(db, club)
    return club
