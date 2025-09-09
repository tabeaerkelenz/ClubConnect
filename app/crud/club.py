from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from ClubConnect.app.db.models import Club
from ClubConnect.app.schemas.club import ClubCreate, ClubUpdate

def create_club(db: Session, data: ClubCreate) -> Club:
    club = Club(name=data.name)
    db.add(club)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Could not create club") from e
    db.refresh(club)
    return club

def get_club(db: Session, club_id: int) -> Club | None:
    return db.get(Club, club_id)

def list_clubs(db: Session, skip: int = 0, limit: int = 50, q: Optional[str] = None) -> list[Club]:
    limit = min(limit, 200)
    stmt = (
        select(Club)
        .order_by(Club.id.asc())
        .offset(skip)
        .limit(limit)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Club.name.ilike(like))
    stmt = stmt.order_by(Club.id.asc()).offset(skip).limit(limit)
    result = db.execute(stmt).scalars().all()
    return list(result)

def update_club(db: Session, club_id: int, data: ClubUpdate) -> Club | None:
    club = db.get(Club, club_id)
    if not club:
        return None

    if data.name is not None:
        club.name = data.name

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise ValueError("Could not update club") from e

    db.refresh(club)
    return club

def delete_club(db: Session, club_id: int) -> Club | None:
    results = db.get(Club, club_id)
    if not results:
        return None
    if results:
        db.delete(results)
    db.commit()
    return results
