from __future__ import annotations
from datetime import datetime

from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
from app.repositories.attendance import AttendanceRepository
from app.services.membership import MembershipService
from app.exceptions.base import InvalidTimeRange, AttendanceNotFoundError


class AttendanceService:
    def __init__(
        self,
        attendance_repo: AttendanceRepository,
        membership_service: MembershipService,
    ) -> None:
        self.attendances = attendance_repo
        self.memberships = membership_service

    @staticmethod
    def _validate_time_range(checked_in_at: datetime | None, checked_out_at: datetime | None) -> None:
        if checked_in_at and checked_out_at and checked_out_at < checked_in_at:
            raise InvalidTimeRange()

    def create(
        self,
        *,
        club_id: int,
        session_id: int,
        user_id: int,
        me_id: int,
        data: AttendanceCreate,
    ):
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        self.memberships.require_member_of_club(user_id, club_id)

        self._validate_time_range(data.checked_in_at, data.checked_out_at)

        return self.attendances.create(
            session_id=session_id,
            user_id=user_id,
            status=data.status or "present",
            recorded_by_id=me_id,
            checked_in_at=data.checked_in_at,
            checked_out_at=data.checked_out_at,
            note=data.note,
        )

    def list_by_session(
        self,
        *,
        club_id: int,
        session_id: int,
        me_id: int,
        skip: int = 0,
        limit: int = 50,
    ):
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        return self.attendances.list_by_session_in_club(
            club_id=club_id,
            session_id=session_id,
            skip=skip,
            limit=limit,
        )

    def get(
        self,
        *,
        club_id: int,
        attendance_id: int,
        me_id: int,
    ):
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        return self.attendances.get_in_club(club_id=club_id, attendance_id=attendance_id)

    def update(
        self,
        *,
        club_id: int,
        attendance_id: int,
        session_id: int,
        me_id: int,
        data: AttendanceUpdate,
    ):
        self.memberships.require_coach_or_owner_of_club(me_id, club_id)
        self._validate_time_range(data.checked_in_at, data.checked_out_at)

        att = self.attendances.get_in_club(club_id=club_id, attendance_id=attendance_id)
        if att.session_id != session_id:
            raise AttendanceNotFoundError()

        return self.attendances.update(att, data=data)
