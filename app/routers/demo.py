from datetime import datetime, date, timedelta, timezone
import os
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db

from app.schemas.session import SessionCreate
from app.schemas.club import ClubCreate
from app.schemas.plan import PlanCreate
# Services
from app.services import user as user_service
from app.services import club as club_service
from app.services import membership as membership_service
from app.services import plan as plan_service
from app.services import session as session_service
from app.services import exercise as exercise_service

router = APIRouter(prefix="/demo", tags=["demo"])

def _require_demo_key(x_demo_key: str | None):
    """Protect the demo endpoint with an optional API key.
    Set DEMO_API_KEY in Render; if unset, no auth is enforced."""
    expected = settings.DEMO_API_KEY
    if expected and x_demo_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid demo key")

@router.post("/run")
def run_demo(
    db: Session = Depends(get_db),
    x_demo_key: str | None = Header(default=None, convert_underscores=True),
):
    _require_demo_key(x_demo_key)

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    # 1) Users
    coach = user_service.create_user_service(db, name="Coach Carla", email=f"coach_{ts}@example.com", password="Password123")
    athlete = user_service.create_user_service(db, name="Athlete Alex", email=f"athlete_{ts}@example.com", password="Password123")

    # 2) Club
    club = club_service.create_club_service(db, payload=ClubCreate(name=f"Demo Club {ts}"), user=coach)

    # 3) Memberships
    membership = membership_service.create_membership_service(db, club_id=club.id, email=athlete.email, role="coach")

    # 4) Plan
    plan = plan_service.create_plan_service(db, club_id=club.id, me=coach, data=PlanCreate(name="Intro Plan", description="A starter plan created by the demo endpoint.", plan_type="club"))

    # 5) Session
    now_utc = datetime.now(timezone.utc)
    starts_at = now_utc.replace(hour=18, minute=0, second=0, microsecond=0)
    ends_at = starts_at + timedelta(hours=1)

    sess_in = SessionCreate(
        name="Intro Session",
        description="A beginner-friendly session to get started.",
        starts_at=starts_at.isoformat(),  # e.g. "2025-09-21T18:00:00+00:00"
        ends_at=ends_at.isoformat(),
        location="Campus Gym",
        note="Intro session from demo endpoint",
    )
    sess = exercise_service.create_exercise(db, club_id=club.id, plan_id=plan.id, me=coach, data=sess_in)

    return {
        "message": "Demo data created ✅",
        "coach": {"id": coach.id, "email": coach.email},
        "athlete": {"id": athlete.id, "email": athlete.email},
        "club": {"id": club.id, "name": club.name},
        "membership": {"id": getattr(membership, "id", None), "role": getattr(membership, "role", None)},
        "plan": {"id": plan.id, "name": plan.name},
        "session": {"id": getattr(sess, "id", None), "location": getattr(sess, "location", None)},
    }
