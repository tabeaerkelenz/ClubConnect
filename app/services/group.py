from __future__ import annotations

from app.models.models import Group
from app.repositories.group import GroupRepository
from app.schemas.group import GroupCreate, GroupUpdate
from app.services.membership import MembershipService


class GroupService:
    def __init__(
        self,
        group_repo: GroupRepository,
        membership_service: MembershipService,
    ) -> None:
        self.groups = group_repo
        self.memberships = membership_service

    def create(self, *, actor_id: int, club_id: int, data: GroupCreate) -> Group:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)
        return self.groups.create(
            club_id=club_id,
            name=data.name,
            description=data.description,
            created_by_id=actor_id,
        )

    def get(self, *, actor_id: int, club_id: int, group_id: int) -> Group:
        self.memberships.require_member_of_club(actor_id, club_id)
        return self.groups.get_by_id(club_id=club_id, group_id=group_id)

    def list(
        self,
        *,
        actor_id: int,
        club_id: int,
        q: str | None,
        offset: int,
        limit: int,
    ) -> list[Group]:
        self.memberships.require_member_of_club(actor_id, club_id)
        return self.groups.list(club_id=club_id, q=q, offset=offset, limit=limit)

    def update(self, *, actor_id: int, club_id: int, group_id: int, data: GroupUpdate) -> Group:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)
        return self.groups.update(
            club_id=club_id,
            group_id=group_id,
            name=data.name,
            description=data.description,
        )

    def delete(self, *, actor_id: int, club_id: int, group_id: int) -> None:
        self.memberships.require_coach_or_owner_of_club(actor_id, club_id)
        self.groups.delete(club_id=club_id, group_id=group_id)
