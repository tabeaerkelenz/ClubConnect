from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.models import Group


def create_group(db: Session, *, club_id: int, name: str, description: str, created_by_id:int) -> Group:
    """Create a new group."""
    group = Group(club_id=club_id, name=name, description=description, created_by_id=created_by_id,)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

def get_group_by_id(db: Session, group_id: int) -> Group | None:
    """Get a group by its ID."""
    return db.get(Group, group_id)

def list_search_groups(db: Session, club_id: int, q: str | None, limit: int, offset: int) -> Group | None:
    """Get a group by its name."""
    stmt = select(Group).where(Group.club_id == club_id)
    if q:
        filter= f"%{q}%"
        stmt = stmt.where(Group.name.ilike(filter))
    stmt = stmt.order_by(Group.name.asc()).offset(offset).limit(limit)
    return db.execute(stmt).scalars().all()

