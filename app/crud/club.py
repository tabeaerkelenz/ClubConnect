from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Club, Membership


def add_membership(db, user_id, club_id, role):
    membership = Membership(user_id=user_id, club_id=club_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership

def create_club(db: Session, name: str) -> Club:
    club = Club(name=name)
    db.add(club)
    db.commit()
    db.refresh(club)
    return club

def get_club(db: Session, club_id: int) -> Club | None:
    return db.get(Club, club_id)

def list_clubs(db: Session, skip: int = 0, limit: int = 50, q: str | None = None) -> list[Club]:
    stmt = select(Club)

    if q:
        stmt = stmt.where(Club.name.ilike(f"%{q.strip}%"))
    stmt = stmt.order_by(Club.name.asc()).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()

def get_clubs_by_user(db: Session, user_id: int):
    return (
        db.query(Club)
        .join(Membership, Membership.club_id == Club.id)
        .filter(Membership.user_id == user_id)
        .order_by(Club.name.asc())
        .all()
    )

def update_club(db: Session, club: Club, name: str) -> Club | None:
    if name is not None:
        club.name = name
    db.commit()
    db.refresh(club)
    return club

def delete_club(db: Session, club: Club) -> Club | None:
    db.delete(club)
    db.commit()
