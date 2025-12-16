from __future__ import annotations

from app.models.models import GroupMembership
from app.repositories.group_membership import GroupMembershipRepository
from app.services.membership import MembershipService


class GroupMembershipService:
    def __init__(
        self,
        gm_repo: GroupMembershipRepository,
        membership_service: MembershipService,
    ) -> None:
        self.gms = gm_repo
        self.memberships = membership_service

    def list_members(self, *, actor_id: int, club_id: int, group_id: int) -> list[GroupMembership]:
        self.memberships.require_member_of_club(actor_id, club_id)
        return self.gms.list_for_group(club_id=club_id, group_id=group_id)

    def add_member(
        self,
        *,
        actor_id: int,
        club_id: int,
        group_id: int,
        user_id: int,
        role: str | None,
    ) -> GroupMembership:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)

        # Business rule: can only add club members to groups
        self.memberships.require_member_of_club(user_id, club_id)

        return self.gms.add(club_id=club_id, group_id=group_id, user_id=user_id, role=role)

    def set_member_role(
        self,
        *,
        actor_id: int,
        club_id: int,
        group_id: int,
        user_id: int,
        role: str | None,
    ) -> GroupMembership:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)
        self.memberships.require_member_of_club(user_id, club_id)
        return self.gms.set_role(club_id=club_id, group_id=group_id, user_id=user_id, role=role)

    def remove_member(self, *, actor_id: int, club_id: int, group_id: int, user_id: int) -> None:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)
        return self.gms.remove(club_id=club_id, group_id=group_id, user_id=user_id)
