from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    DateTime,
    UniqueConstraint,
    Index,
    Text,
    Boolean,
    text, func, CheckConstraint,
)
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
    owner = "owner"


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


class PlanAssigneeRole(enum.Enum):
    coach = "coach"
    athlete = "athlete"


class AttendanceStatus(enum.Enum):
    present = "present"
    excused = "excused"
    absent = "absent"
    late = "late"


# –––––––––– Mixins –––––––––––


class TimestampMixin:
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# –––––––––– Models –––––––––––


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(250), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    memberships = relationship(
        "Membership", foreign_keys="Membership.user_id", back_populates="user", cascade="all, delete-orphan"
    )
    plans = relationship(
        "Plan", back_populates="created_by", foreign_keys="Plan.created_by_id"
    )
    sessions = relationship(
        "Session", back_populates="user", foreign_keys="Session.created_by"
    )
    recorded_attendances = relationship("Attendance", foreign_keys="Attendance.recorded_by_id", back_populates="recorded_by", lazy="selectin")

    group_memberships = relationship(
        "GroupMembership",
        foreign_keys="GroupMembership.user_id",
        back_populates="user",
        lazy="selectin",
    )

    assigned_plan_assignments = relationship(
        "PlanAssignee",
        back_populates="assigned_by",
        foreign_keys="PlanAssignee.assigned_by_id",
        lazy="selectin",
    )

    plan_assignments_as_target = relationship(
        "PlanAssignee",
        back_populates="user",
        foreign_keys="PlanAssignee.user_id",
        lazy="selectin",
    )

    attendances = relationship(
        "Attendance",
        foreign_keys="Attendance.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def password(self):
        raise AttributeError("Password is write-only")

    @password.setter
    def password(self, plain: str):
        from app.core.security import hash_password

        self.password_hash = hash_password(plain)

    def check_password(self, plain: str) -> bool:
        from app.core.security import verify_password

        return verify_password(plain, self.password_hash)


class Club(Base, TimestampMixin):
    __tablename__ = "clubs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(4), nullable=True)    # ISO-3166-1 alpha-2 (e.g., "DE")
    city: Mapped[str] = mapped_column(String(128), nullable=True)
    sport: Mapped[str] = mapped_column(String(100), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    plans = relationship("Plan", back_populates="club", cascade="all, delete-orphan")
    memberships = relationship(
        "Membership", back_populates="club", cascade="all, delete-orphan"
    )


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"

    # add the mapped and mapped_column here aswell
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    club_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MembershipRole] = mapped_column(Enum(MembershipRole, name="membershiprole"), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="memberships", lazy="selectin")
    club: Mapped["Club"] = relationship("Club", back_populates="memberships")

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
    club_id = Column(
        Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False
    )
    description = Column(Text)
    created_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )

    created_by = relationship(
        "User", back_populates="plans", foreign_keys=[created_by_id]
    )
    club = relationship("Club", back_populates="plans")
    sessions = relationship(
        "Session", back_populates="plan", cascade="all, delete-orphan"
    )
    exercises = relationship(
        "Exercise", back_populates="plan", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_plans_club_id", "club_id"),)


class Exercise(Base, TimestampMixin):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(
        Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
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
    plan_id = Column(
        Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(100), nullable=False)
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship(
        "User", back_populates="sessions", foreign_keys="Session.created_by"
    )
    plan = relationship("Plan", back_populates="sessions")
    attendances = relationship(
        "Attendance", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_sessions_plan_id_starts_at", "plan_id", "starts_at"),)


class PlanAssignee(Base):
    __tablename__ = "plan_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(
        Integer, ForeignKey("plans.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )

    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"))

    role = Column(Enum(PlanAssigneeRole, name="planassignee_role"), nullable=False)
    assigned_by_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at = Column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    # Relationships (no back_populates yet to avoid touching other models right now)
    plan = relationship("Plan")
    user = relationship("User", foreign_keys=[user_id], back_populates="plan_assignments_as_target",
        lazy="selectin",)
    assigned_by = relationship("User", foreign_keys=[assigned_by_id], back_populates="assigned_plan_assignments", lazy="selectin")
    group = relationship("Group", foreign_keys=[group_id], lazy="selectin")

    __table_args__ = (
        UniqueConstraint("plan_id", "user_id", name="uq_plan_assignees_plan_user"),
        UniqueConstraint("plan_id", "group_id", name="uq_plan_assignees_plan_group"),

        CheckConstraint(
            "(user_id IS NOT NULL) <> (group_id IS NOT NULL)",
            name="ck_plan_assignment_one_target",
        ),

        Index("ix_plan_assignments_plan_id", "plan_id"),
        Index("ix_plan_assignments_user_id", "user_id"),
    )

PlanAssignment = PlanAssignee


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(Enum(AttendanceStatus, name="attendancestatus"), nullable=False, server_default="present")

    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_out_at = Column(DateTime(timezone=True), nullable=True)
    recorded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text(), nullable=True)

    session = relationship("Session", back_populates="attendances", lazy="selectin")
    user = relationship("User", foreign_keys=[user_id],back_populates="attendances", lazy="selectin")
    recorded_by = relationship("User", foreign_keys=[recorded_by_id], back_populates="recorded_attendances", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("session_id", "user_id", name="uq_attendance_session_user"),
        Index("ix_attendance_session_id", "session_id"),
        Index("ix_attendance_user_id", "user_id"),
    )


class Group(Base):
    __tablename__ = "groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str | None]
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    memberships = relationship(
        "GroupMembership",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (UniqueConstraint("club_id", "name", name="uq_group_name_per_club"),)


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int]  = mapped_column(ForeignKey("users.id",  ondelete="CASCADE"), primary_key=True)
    role: Mapped[str | None] = mapped_column(String(32))
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="group_memberships", lazy="selectin")
    group: Mapped["Group"] = relationship("Group", back_populates="memberships", lazy="selectin")
