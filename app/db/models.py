from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, UniqueConstraint, Index, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base  # import Base from database.py

# –––––––––– Enums ––––––––––
class UserRole(enum.Enum):
    athlete = "athlete"
    trainer = "trainer"
    admin = "admin"

class MembershipRole(enum.Enum):
    member = "member"
    coach = "coach"

class PlanType(enum.Enum):
    club = "club"
    personal = "personal"

class DayLabel(enum.Enum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"

class AttendanceStatus(enum.Enum):
    present = "present"
    excused = "excused"
    absent = "absent"

# –––––––––– Mixins –––––––––––
class TimestampMixin:
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)

# –––––––––– Models –––––––––––
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(250), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="user", foreign_keys="Plan.created_by")
    sessions = relationship("Session", back_populates="user", foreign_keys="Session.created_by")
    attendances = relationship("Attendance", back_populates="user")

class Club(Base, TimestampMixin):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    plans = relationship("Plan", back_populates="club", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="club", cascade="all, delete-orphan")

class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"

# add the mapped and mapped_column here aswell
    id = Column(Integer, primary_key=True, autoincrement=True)
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False,)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,)
    role = Column(Enum(MembershipRole), nullable=False)

    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("club_id", "user_id", name="uq_membership_club_user"),
        Index("ix_memberships_user_id", "user_id"),
        Index("ix_memberships_club_id", "club_id"),
    )

class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    plan_type = Column(Enum(PlanType), nullable=False)  # club, personal
    club_id = Column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    user = relationship("User", back_populates="plans", foreign_keys=[created_by])
    club = relationship("Club", back_populates="plans")
    sessions = relationship("Session", back_populates="plan", cascade="all, delete-orphan")
    exercises = relationship("Exercise", back_populates="plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_plans_club_id", "club_id"),
    )

class Exercise (Base, TimestampMixin):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    sets = Column(Integer)
    repetitions = Column(Integer)
    position = Column(Integer)
    day_label = Column(Enum(DayLabel), nullable=True)

    plan = relationship("Plan", back_populates="exercises")

    __table_args__ = (
        Index("ix_exercises_plan_id", "plan_id"),
        UniqueConstraint("plan_id", "position", name="uq_exercises_plan_position"),
    )

class Session(Base, TimestampMixin):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(100), nullable=False)
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="sessions", foreign_keys="Session.created_by")
    plan = relationship("Plan", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sessions_plan_id_starts_at", "plan_id", "starts_at"),
    )

class Attendance (Base, TimestampMixin):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)

    session = relationship("Session", back_populates="attendances")
    user = relationship("User", back_populates="attendances")

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_attendance_session_user"),
        Index("ix_attendance_session_id", "session_id"),
        Index("ix_attendance_user_id", "user_id"),
    )