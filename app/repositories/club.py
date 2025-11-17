from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.exceptions.base import MembershipExistsError, DuplicateSlugError, ClubNotFoundError
from app.models.models import Club, Membership


class ClubRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_membership(self, user_id, club_id, role):
        """Add a user to a club with a specific role."""
        membership = Membership(user_id=user_id, club_id=club_id, role=role)
        try:
            self.db.add(membership)
            self.db.commit()
            self.db.refresh(membership)
            return membership
        except IntegrityError as e:
            self.db.rollback()
            raise MembershipExistsError


    def create_club(self, **kwargs) -> Club | None:
        """Create a new club."""
        club = Club(**kwargs)
        try:
            self.db.add(club)
            self.db.flush()
            return club
        except IntegrityError as e:
            self.db.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                raise DuplicateSlugError

    def get_club(self, club_id: int) -> Club | None:
        """Get a club by its ID."""
        try:
            return self.db.get(Club, club_id)
        except IntegrityError as e:
            if "Not found" in str(e):
                raise ClubNotFoundError


    def list_clubs(
        self, skip: int = 0, limit: int = 50, q: str | None = None
    ) -> list[Club]:
        """List or search clubs with optional pagination and name filtering."""
        stmt = select(Club)

        if q:
            stmt = stmt.where(Club.name.contains(q, autoescape=True))

        stmt = stmt.order_by(Club.name.asc()).offset(skip).limit(limit)
        return self.db.execute(stmt).scalars().all()


    def get_clubs_by_user(self, user_id: int):
        """Get all clubs a user is a member of."""
        return (
            self.db.query(Club)
            .join(Membership, Membership.club_id == Club.id)
            .filter(Membership.user_id == user_id)
            .order_by(Club.name.asc())
            .all()
        )


    def update_club(self, club: Club, **kwargs) -> Club | None:
        """Update a club's name."""
        try:
            for key, value in kwargs.items():
                setattr(club, key, value)
            self.db.commit()
            return club
        except IntegrityError as e:
            if "duplicate key value violates unique constraint" in str(e):
                raise DuplicateSlugError

    def delete_club(self, club: Club) -> Club | None:
        """Delete a club."""
        try:
            self.db.delete(club)
            self.db.commit()
        except IntegrityError as e:
            if "Not found" in str(e):
                raise ClubNotFoundError
