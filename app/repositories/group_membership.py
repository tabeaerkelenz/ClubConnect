from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.base import (
    GroupMembershipExistsError,
    GroupMembershipNotFoundError,
    GroupNotFoundError,
)
from app.models.models import Group, GroupMembership


class GroupMembershipRepository:
    """Persistence-only. Club-scoped access via Group join."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _ensure_group_in_club(self, *, club_id: int, group_id: int) -> None:
        stmt = select(Group.id).where(Group.id == group_id, Group.club_id == club_id)
        exists = self.db.execute(stmt).scalar_one_or_none()
        if not exists:
            raise GroupNotFoundError()

    def list_for_group(self, *, club_id: int, group_id: int) -> list[GroupMembership]:
        self._ensure_group_in_club(club_id=club_id, group_id=group_id)

        stmt = (
            select(GroupMembership)
            .where(GroupMembership.group_id == group_id)
            .order_by(GroupMembership.user_id.asc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get(self, *, club_id: int, group_id: int, user_id: int) -> GroupMembership:
        self._ensure_group_in_club(club_id=club_id, group_id=group_id)

        stmt = select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
        )
        gm = self.db.execute(stmt).scalar_one_or_none()
        if not gm:
            raise GroupMembershipNotFoundError()
        return gm

    def add(
        self,
        *,
        club_id: int,
        group_id: int,
        user_id: int,
        role: str | None,
    ) -> GroupMembership:
        self._ensure_group_in_club(club_id=club_id, group_id=group_id)

        gm = GroupMembership(group_id=group_id, user_id=user_id, role=role)
        self.db.add(gm)
        try:
            self.db.commit()
            self.db.refresh(gm)
            return gm
        except IntegrityError as e:
            self.db.rollback()
            # likely PK conflict (group_id,user_id)
            raise GroupMembershipExistsError() from e

    def set_role(
        self,
        *,
        club_id: int,
        group_id: int,
        user_id: int,
        role: str | None,
    ) -> GroupMembership:
        gm = self.get(club_id=club_id, group_id=group_id, user_id=user_id)
        gm.role = role
        self.db.commit()
        self.db.refresh(gm)
        return gm

    def remove(self, *, club_id: int, group_id: int, user_id: int) -> None:
        self._ensure_group_in_club(club_id=club_id, group_id=group_id)

        # Make deletion “honest”: raise if nothing was deleted
        stmt = delete(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
        )
        res = self.db.execute(stmt)
        if res.rowcount == 0:
            self.db.rollback()
            raise GroupMembershipNotFoundError()

        self.db.commit()
