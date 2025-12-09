from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as SASession

from app.models.models import Membership, MembershipRole
from app.exceptions.base import MembershipExistsError


class MembershipRepository:
    """Persistence-only access for Memberships.

    - Knows about SQLAlchemy Session and IntegrityError.
    - Maps DB integrity errors to domain errors (MembershipExistsError).
    - No FastAPI, no HTTPExceptions, no business decisions.
    """

    def __init__(self, db: SASession) -> None:
        self.db = db


    # ---- Basic loaders ----

    def get(self, membership_id: int) -> Optional[Membership]:
        """Return a membership by ID, or None if not found."""
        return self.db.get(Membership, membership_id)

    def get_by_club_and_user(self, club_id: int, user_id: int) -> Optional[Membership]:
        """Return the membership of a given user in a given club, or None."""
        stmt = select(Membership).where(
            Membership.club_id == club_id,
            Membership.user_id == user_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_for_user(self, user_id: int) -> list[Membership]:
        """Return all memberships for a given user."""
        stmt = select(Membership).where(Membership.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def list_for_club(self, club_id: int) -> list[Membership]:
        """Return all memberships for a given club."""
        stmt = select(Membership).where(Membership.club_id == club_id)
        return list(self.db.execute(stmt).scalars().all())


    # ---- Mutations (commit inside) ----
    def create(
        self,
        club_id: int,
        user_id: int,
        role: MembershipRole,
    ) -> Membership:
        """
        Create a membership and commit.

        DB-level unique (club_id, user_id) violation → MembershipExistsError.
        """
        membership = Membership(club_id=club_id, user_id=user_id, role=role)
        self.db.add(membership)
        self._commit_with_membership_guard()
        # Ensure we have fresh state (e.g. timestamps, defaults)
        self.db.refresh(membership)
        return membership

    def update_role(
        self,
        membership: Membership,
        new_role: MembershipRole,
    ) -> Membership:
        """Update the role of a membership and commit."""
        membership.role = new_role
        self._commit_with_membership_guard()
        self.db.refresh(membership)
        return membership

    def delete(self, membership: Membership) -> None:
        """Delete a membership and commit."""
        self.db.delete(membership)
        self._commit_with_membership_guard()


    # ---- Counts / helpers for business rules ----
    def count_coach_owner(
        self,
        club_id: int,
        exclude_user_id: Optional[int] = None,
    ) -> int:
        """
        Count memberships with role in {coach, owner} for a club.

        If exclude_user_id is given, that user's membership is excluded.
        Used for 'last coach/owner' protection in the service layer.
        """
        roles = [MembershipRole.coach, MembershipRole.owner]

        stmt = (
            select(func.count())
            .select_from(Membership)
            .where(
                Membership.club_id == club_id,
                Membership.role.in_(roles),
            )
        )

        if exclude_user_id is not None:
            stmt = stmt.where(Membership.user_id != exclude_user_id)

        count = self.db.scalar(stmt)
        return int(count or 0)


    # ---- Internal: commit + integrity mapping ----
    def _commit_with_membership_guard(self) -> None:
        """
        Commit and map DB integrity errors to domain errors.

        - uq_membership_club_user → MembershipExistsError

        All other IntegrityErrors are re-raised.
        """
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            msg = str(getattr(e.orig, "args", e.orig) or e).lower()
            # Depending on how postgres+sqlalchemy report the error, we look for
            # the constraint name or parts of the message.
            if "uq_membership_club_user" in msg:
                raise MembershipExistsError() from e
            # if I also see "unique constraint" with table/columns instead;
            raise
