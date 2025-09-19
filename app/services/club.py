from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from ClubConnect.app.crud import club as crud
from ClubConnect.app.crud.club import get_clubs_by_user, create_club, add_membership
from ClubConnect.app.db.models import MembershipRole
from ClubConnect.app.schemas.club import ClubUpdate

def create_club_service(db, payload, user):
    try:
        club = create_club(db, payload.name)
        add_membership(db, user.id, club.id, MembershipRole.coach)
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

def update_club_service(db, club_id: int, data: ClubUpdate):
    club = crud.get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    try:
        return crud.update_club(db, club, data.name)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Club name already exists")

def delete_club_service(db, club_id: int):
    club = crud.get_club(db, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    crud.delete_club(db, club)
    return club
