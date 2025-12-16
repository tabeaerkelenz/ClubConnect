from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.base import GroupNameExistsError, GroupNotFoundError
from app.models.models import Group


class GroupRepository:
    """Persistence-only. Club-scoped access."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        club_id: int,
        name: str,
        description: str | None,
        created_by_id: int | None,
    ) -> Group:
        group = Group(
            club_id=club_id,
            name=name,
            description=description,
            created_by_id=created_by_id,
        )
        self.db.add(group)
        try:
            self.db.commit()
            self.db.refresh(group)
            return group
        except IntegrityError as e:
            self.db.rollback()
            # uq_group_name_per_club
            if "uq_group_name_per_club" in str(e.orig):
                raise GroupNameExistsError() from e
            raise

    def get_by_id(self, *, club_id: int, group_id: int) -> Group:
        stmt = select(Group).where(Group.id == group_id, Group.club_id == club_id)
        group = self.db.execute(stmt).scalar_one_or_none()
        if not group:
            raise GroupNotFoundError()
        return group

    def list(
        self,
        *,
        club_id: int,
        q: str | None,
        offset: int,
        limit: int,
    ) -> list[Group]:
        stmt = select(Group).where(Group.club_id == club_id)

        if q:
            q_clean = q.strip()
            if q_clean:
                stmt = stmt.where(Group.name.ilike(f"%{q_clean}%"))

        stmt = stmt.order_by(Group.name.asc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def update(
        self,
        *,
        club_id: int,
        group_id: int,
        name: str | None,
        description: str | None,
    ) -> Group:
        group = self.get_by_id(club_id=club_id, group_id=group_id)

        if name is not None:
            group.name = name
        if description is not None:
            group.description = description

        try:
            self.db.commit()
            self.db.refresh(group)
            return group
        except IntegrityError as e:
            self.db.rollback()
            if "uq_group_name_per_club" in str(e.orig):
                raise GroupNameExistsError() from e
            raise

    def delete(self, *, club_id: int, group_id: int) -> None:
        group = self.get_by_id(club_id=club_id, group_id=group_id)
        self.db.delete(group)
        self.db.commit()
