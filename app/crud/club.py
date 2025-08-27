from sqlalchemy.orm import Session
from sqlalchemy import select

from ClubConnect.app.db import models
from ClubConnect.app.db.models import Club
from ClubConnect.app.schemas import club
from ClubConnect.app.schemas.club import ClubCreate, ClubUpdate

def create_club(db: Session, data: ClubCreate) -> models.Club:
    club = models.Club(name=data.name)
    db.add(club)
    db.commit()
    db.refresh(club)
    return club

def get_club(db: Session, club_id: int) -> Club | None:
    stmt = select(Club).where(Club.id == club_id)
    results = db.execute(stmt).scalars().first()
    return results if results else None

def list_clubs(db: Session, skip: int = 0, limit: int = 50) -> list[Club]:
    stmt = (
        select(Club)
        .order_by(Club.id.asc())
        .offset(skip)
        .limit(limit)
    )
    results = db.execute(stmt).scalars().all()
    return results if results else []

def update_club(db: Session, club_id: int, data: ClubUpdate) -> Club | None:
    stmt = select(Club).where(Club.id == club_id)
    club = db.execute(stmt).scalars().first()
    if not club:
        return None

    if data.name is not None:
        club.name = data.name

    db.commit()
    db.refresh(club)
    return club

def delete_club(db: Session, club_id: int) -> Club | None:
    stmt = select(Club).where(Club.id == club_id)
    results = db.execute(stmt).scalars().first()
    if not results:
        return None
    if results:
        db.delete(results)
    db.commit()
    return results
