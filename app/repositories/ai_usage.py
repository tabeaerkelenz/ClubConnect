from __future__ import annotations

from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import AIUsage
from app.exceptions.base import ConflictError


class AIUsageRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- helpers ----------

    @staticmethod
    def _utc_day_start(dt: datetime | None = None) -> datetime:
        """Return UTC start-of-day (00:00:00) for dt or now."""
        now = dt or datetime.now(timezone.utc)
        return now.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # ---------- queries ----------

    def count_today(
        self,
        *,
        user_id: int,
        feature: str,
        club_id: int | None = None,
    ) -> int:
        """
        Count usage rows from UTC start of today for a user+feature.
        If club_id is provided, filter by it as well.
        """
        day_start = self._utc_day_start()

        conditions = [
            AIUsage.user_id == user_id,
            AIUsage.feature == feature,
            AIUsage.created_at >= day_start,
        ]
        if club_id is not None:
            conditions.append(AIUsage.club_id == club_id)

        stmt = sa.select(sa.func.count(AIUsage.id)).where(*conditions)
        return int(self.db.execute(stmt).scalar_one())

    def record(
        self,
        *,
        user_id: int,
        club_id: int,
        feature: str,
    ) -> AIUsage:
        """
        Insert a usage row. Commit/rollback mirrors repo patterns.
        IntegrityError is unlikely here (no unique constraint), but keep the pattern.
        """
        usage = AIUsage(user_id=user_id, club_id=club_id, feature=feature)

        try:
            self.db.add(usage)
            self.db.commit()
            self.db.refresh(usage)
            return usage
        except IntegrityError as e:
            self.db.rollback()
            raise ConflictError("Could not record AI usage") from e
