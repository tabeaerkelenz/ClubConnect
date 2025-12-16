from __future__ import annotations

from app.repositories.session import SessionRepository
from app.services.membership import MembershipService
from app.schemas.session import SessionCreate, SessionUpdate
from app.exceptions.base import InvalidTimeRange


class SessionService:
    def __init__(
        self,
        *,
        session_repo: SessionRepository,
        membership_service: MembershipService,
    ):
        self.session_repo = session_repo
        self.membership_service = membership_service

    # ---------- read ----------

    def list_sessions(
        self, *, club_id: int, plan_id: int, user_id: int
    ):
        self.membership_service.require_member_of_club(
            club_id=club_id, user_id=user_id
        )
        return self.session_repo.list_in_plan(
            club_id=club_id, plan_id=plan_id
        )

    def get_session(
        self, *, club_id: int, plan_id: int, session_id: int, user_id: int
    ):
        self.membership_service.require_member_of_club(
            club_id=club_id, user_id=user_id
        )
        return self.session_repo.get_in_plan(
            club_id=club_id, plan_id=plan_id, session_id=session_id
        )

    # ---------- write ----------

    def create_session(
        self,
        *,
        club_id: int,
        plan_id: int,
        user_id: int,
        data: SessionCreate,
    ):
        self.membership_service.require_coach_or_owner_of_club(
            club_id=club_id, user_id=user_id
        )

        return self.session_repo.create_in_plan(
            club_id=club_id,
            plan_id=plan_id,
            created_by_id=user_id,
            name=data.name,
            description=data.description,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            location=data.location,
            note=data.note,
        )

    def update_session(
        self,
        *,
        club_id: int,
        plan_id: int,
        session_id: int,
        user_id: int,
        data: SessionUpdate,
    ):
        self.membership_service.require_coach_or_owner_of_club(
            club_id=club_id, user_id=user_id
        )

        updates = data.model_dump(exclude_unset=True)

        # business rule: validate final time range
        if "starts_at" in updates or "ends_at" in updates:
            current = self.session_repo.get_in_plan(
                club_id=club_id, plan_id=plan_id, session_id=session_id
            )

            new_starts = updates.get("starts_at", current.starts_at)
            new_ends = updates.get("ends_at", current.ends_at)

            if new_starts >= new_ends:
                raise InvalidTimeRange()

        return self.session_repo.update_in_plan(
            club_id=club_id,
            plan_id=plan_id,
            session_id=session_id,
            updates=updates,
        )

    def delete_session(
        self,
        *,
        club_id: int,
        plan_id: int,
        session_id: int,
        user_id: int,
    ) -> None:
        self.membership_service.require_coach_or_owner_of_club(
            club_id=club_id, user_id=user_id
        )

        self.session_repo.delete_in_plan(
            club_id=club_id,
            plan_id=plan_id,
            session_id=session_id,
        )
