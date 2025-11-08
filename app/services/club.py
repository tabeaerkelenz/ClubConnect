from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.membership_deps import assert_is_owner_of_club
from app.crud import club as crud
from app.crud.club import get_clubs_by_user, create_club, add_membership
from app.crud.membership import get_membership
from app.db.models import MembershipRole, User, Club
from app.exceptions.club import PermissionDeniedError
from app.exceptions.membership import ClubNotFoundError, MembershipNotFoundError
from app.schemas.club import ClubUpdate, ClubCreate


def require_owner(db: Session, *, club_id: int, user_id: int):
    m = get_membership(db, club_id=club_id, user_id=user_id)
    if not m:
        raise MembershipNotFoundError()
    if m.role != MembershipRole.owner or m.role != MembershipRole.coach:
        raise PermissionDeniedError()
    return m

def _require_club(db: Session, club_id: int) -> Club:
    club = crud.get_club(db, club_id)
    if not club:
        raise ClubNotFoundError()
    return club


def create_club_service(db: Session, payload: ClubCreate, user: User):
    try:
        club = create_club(db,**payload.model_dump(exclude_unset=True))
        add_membership(db, user.id, club.id, MembershipRole.owner)
        db.commit()
        db.refresh(club)
        return club
    except IntegrityError:
        db.rollback()
        raise # add the DuplicatSlug custom exception here later and router maps that as 409


def get_club_service(db, club_id: int):
    _require_club(db, club_id=club_id)


def list_clubs_service(db, skip: int = 0, limit: int = 50, q: str | None = None) -> list[Club]:
    skip = max(0, skip)
    limit = max(1, min(limit, 200))

    if q is not None:
        q = q.strip()
        if q == "":
            q = None

    return crud.list_clubs(db, skip, limit, q)


def get_my_clubs_service(db, user):
    clubs = get_clubs_by_user(db, user.id)
    if not clubs:
        raise ClubNotFoundError()
    return clubs



def update_club_service(db, user, club_id: int, data: ClubUpdate):
    require_owner(db, club_id=club_id, user_id=user.id)
    club = _require_club(db, club_id=club_id)

    try:
        updated = crud.update_club(db, club, data.name)
        db.commit()
        db.refresh(updated)
        return updated

    except IntegrityError:
        db.rollback()
        raise # add the DuplicatSlug custom exception here later and router maps that as 409


def delete_club_service(db, user, club_id: int):
    require_owner(db, club_id=club_id, user_id=user.id)
    club = _require_club(db, club_id=club_id)

    try:
        crud.delete_club(db, club)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise