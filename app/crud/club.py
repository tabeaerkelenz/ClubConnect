from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Club, Membership


def add_membership(db, user_id, club_id, role):
    """Add a user to a club with a specific role."""
    membership = Membership(user_id=user_id, club_id=club_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def create_club(db: Session,
    *,
    name: str,
    country: str | None = None,
    city: str | None = None,
    sport: str | None = None,
    founded_year: int | None = None,
    description: str | None = None,
) -> Club:
    """Create a new club."""
    club = Club(name=name,
        country=country,
        city=city,
        sport=sport,             # <-- matches column name
        founded_year=founded_year,
        description=description,
    )
    db.add(club)
    db.flush()
    return club


def get_club(db: Session, club_id: int) -> Club | None:
    """Get a club by its ID."""
    return db.get(Club, club_id)


def list_clubs(
    db: Session, skip: int = 0, limit: int = 50, q: str | None = None
) -> list[Club]:
    """List or search clubs with optional pagination and name filtering."""
    stmt = select(Club)

    if q:
        stmt = stmt.where(Club.name.contains(q, autoescape=True))

    stmt = stmt.order_by(Club.name.asc()).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def get_clubs_by_user(db: Session, user_id: int):
    """Get all clubs a user is a member of."""
    return (
        db.query(Club)
        .join(Membership, Membership.club_id == Club.id)
        .filter(Membership.user_id == user_id)
        .order_by(Club.name.asc())
        .all()
    )


def update_club(db: Session, club: Club, name: str) -> Club | None:
    """Update a club's name."""
    if name is not None:
        club.name = name
    db.commit()
    db.refresh(club)
    return club


def delete_club(db: Session, club: Club) -> Club | None:
    """Delete a club."""
    db.delete(club)
    db.commit()
