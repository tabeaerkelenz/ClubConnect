from typing import List

from app.models.models import Membership, MembershipRole
from app.repositories.membership import MembershipRepository
from app.repositories.user import UserRepository
from app.repositories.club import ClubRepository
from app.exceptions.base import (
    UserNotFoundError,
    ClubNotFoundError,
    MembershipNotFoundError,
    MembershipExistsError,
    NotClubMember,
    CoachRequiredError,
    OwnerRequiredError,
    CoachOrOwnerRequiredError,
    LastCoachViolationError,
)


class MembershipService:
    """Business logic for memberships.

    - No SQLAlchemy Session.
    - No FastAPI or HTTPException.
    - Raises domain errors only.
    """

    def __init__(
        self,
        membership_repo: MembershipRepository,
        user_repo: UserRepository,
        club_repo: ClubRepository,
    ) -> None:
        self.memberships = membership_repo
        self.users = user_repo
        self.clubs = club_repo


    # Creation / listing
    def add_member_by_email(
        self,
        club_id: int,
        email: str,
        role: MembershipRole,
    ) -> Membership:
        """Add a user (by email) to a club with a given role."""

        normalized_email = email.strip().lower()

        user = self.users.get_by_email(normalized_email)
        if not user:
            raise UserNotFoundError()

        club = self.clubs.get_club(club_id)
        if not club:
            raise ClubNotFoundError()

        # Optional explicit check for nicer error than repo duplicate
        existing = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user.id)
        if existing:
            raise MembershipExistsError()

        # Repo commit + integrity-mapping (uq_membership_club_user) happens here
        return self.memberships.create(club_id=club_id, user_id=user.id, role=role)

    def list_user_memberships_by_email(self, email: str) -> List[Membership]:
        """List all memberships for me/the active user."""
        normalized_email = email.strip().lower()

        user = self.users.get_by_email(normalized_email)
        if not user:
            raise UserNotFoundError()

        return self.memberships.list_for_user(user.id)

    def list_club_memberships(self, club_id: int) -> List[Membership]:
        """List all memberships for a given club."""
        club = self.clubs.get_club(club_id)
        if not club:
            raise ClubNotFoundError()

        return self.memberships.list_for_club(club_id)

    def get_membership_for_user_in_club(self, club_id: int, user_id: int) -> Membership:
        """Return a specific user's membership in a club, or raise if missing."""
        membership = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user_id)
        if not membership:
            raise MembershipNotFoundError()
        return membership


    # Role changes / deletion with last-coach protection
    def change_role(
        self,
        club_id: int,
        membership_id: int,
        new_role: MembershipRole,
    ) -> Membership:
        """
        Change a member's role in a club.

        Enforces 'last coach/owner' protection:
        - If current role is coach/owner and new_role is not, ensure there is
          at least one other coach/owner left in the club.
        """

        membership = self.memberships.get(membership_id)
        # Avoid cross-club tampering
        if not membership or membership.club_id != club_id:
            raise MembershipNotFoundError()

        # If we are demoting from coach/owner to a non-coach/owner role, check
        # that there is at least one other coach/owner remaining.
        currently_leading = membership.role in (MembershipRole.coach, MembershipRole.owner)
        becoming_non_leader = new_role not in (MembershipRole.coach, MembershipRole.owner)

        if currently_leading and becoming_non_leader:
            remaining = self.memberships.count_coach_owner(
                club_id=club_id,
                exclude_user_id=int(membership.user_id),
            )
            if remaining == 0:
                raise LastCoachViolationError()

        return self.memberships.update_role(membership, new_role)

    def remove_member(self, club_id: int, membership_id: int) -> None:
        """
        Remove a member from a club.

        Enforces 'last coach/owner' protection:
        - If the membership to delete is coach/owner, ensure there is at least
          one other coach/owner remaining in the club.
        """

        membership = self.memberships.get(membership_id)
        if not membership or membership.club_id != club_id:
            raise MembershipNotFoundError()

        if membership.role in (MembershipRole.coach, MembershipRole.owner):
            remaining = self.memberships.count_coach_owner(
                club_id=club_id,
                exclude_user_id=int(membership.user_id),
            )
            if remaining == 0:
                raise LastCoachViolationError()

        self.memberships.delete(membership)


    # Guard helpers (replacing membership_deps logic)
    def require_member_of_club(self, user_id: int, club_id: int) -> Membership:
        """
        Ensure the user is at least a member of the club.

        member / coach / owner all count as 'member' in this sense.
        """
        membership = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user_id)
        if not membership:
            raise NotClubMember()
        return membership

    def require_coach_of_club(self, user_id: int, club_id: int) -> Membership:
        """Ensure the user is a coach of the club."""
        membership = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user_id)
        if not membership:
            raise NotClubMember()
        if membership.role != MembershipRole.coach:
            raise CoachRequiredError()
        return membership

    def require_owner_of_club(self, user_id: int, club_id: int) -> Membership:
        """Ensure the user is an owner of the club."""
        membership = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user_id)
        if not membership:
            raise NotClubMember()
        if membership.role != MembershipRole.owner:
            raise OwnerRequiredError()
        return membership

    def require_coach_or_owner_of_club(self, user_id: int, club_id: int) -> Membership:
        """Ensure the user is either a coach or an owner of the club."""
        membership = self.memberships.get_by_club_and_user(club_id=club_id, user_id=user_id)
        if not membership:
            raise NotClubMember()
        if membership.role not in (MembershipRole.coach, MembershipRole.owner):
            raise CoachOrOwnerRequiredError()
        return membership
