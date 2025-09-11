from typing import Optional, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func

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
    # clamp + guard
    skip = max(0, skip)
    limit = max(1, min(limit, 200))

    stmt = select(Club)

    if q is not None:
        q_norm = q.strip()
        if q_norm:  # only filter if something remains after trimming
            stmt = stmt.where(Club.name.ilike(f"%{q_norm}%"))

    stmt = stmt.order_by(Club.name.asc()).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()

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
