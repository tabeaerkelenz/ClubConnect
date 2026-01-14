"""baseline schema v2 (with groups, XOR assignments, attendance fields)

Revision ID: 8bdceb080455
Revises: 8f5b7b8c9726
Create Date: 2025-09-24 12:21:59.459199
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8bdceb080455"
down_revision: Union[str, Sequence[str], None] = "8f5b7b8c9726"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- 1) Guarded enum creation (idempotent) -----------------------------------
def _ensure_enums_exist() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
                CREATE TYPE userrole AS ENUM ('athlete','trainer','admin');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'membershiprole') THEN
                -- values must match what's already in prod if it exists
                CREATE TYPE membershiprole AS ENUM ('athlete','coach');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plantype') THEN
                CREATE TYPE plantype AS ENUM ('club','personal');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'daylabel') THEN
                -- short weekday labels (align with your models)
                CREATE TYPE daylabel AS ENUM ('mon','tue','wed','thu','fri','sat','sun');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'planassignee_role') THEN
                CREATE TYPE planassignee_role AS ENUM ('coach','athlete');
            END IF;

            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attendancestatus') THEN
                CREATE TYPE attendancestatus AS ENUM ('present','excused','absent');
            END IF;
        END$$;
        """
    )


def upgrade() -> None:
    """Upgrade schema."""

    # Make sure all enums exist exactly once.
    _ensure_enums_exist()

    # --- 2) Reuse named enums without re-creating them on table create --------
    userrole = postgresql.ENUM(
        "athlete", "trainer", "admin", name="userrole", create_type=False
    )

    membershiprole = postgresql.Enum(
        "athlete", "coach", name="membershiprole", native_enum=True, create_type=False
    )
    plantype = postgresql.Enum("club", "personal", name="plantype", native_enum=True, create_type=False)
    daylabel = postgresql.Enum(
        "mon", "tue", "wed", "thu", "fri", "sat", "sun",
        name="daylabel", native_enum=True, create_type=False
    )
    planassignee_role = postgresql.Enum(
        "coach", "athlete", name="planassignee_role", native_enum=True, create_type=False
    )
    attendancestatus = postgresql.Enum(
        "present", "excused", "absent", name="attendancestatus", native_enum=True, create_type=False
    )

    # ---- Core tables ----
    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=250), nullable=False),
        sa.Column("role", userrole, nullable=False, server_default="athlete"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # ---- Groups & Group Memberships ----
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("club_id", "name", name="uq_group_name_per_club"),
    )
    op.create_index("ix_groups_club_id", "groups", ["club_id"])

    op.create_table(
        "group_memberships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
    op.create_index("ix_group_memberships_group_id", "group_memberships", ["group_id"])
    op.create_index("ix_group_memberships_user_id", "group_memberships", ["user_id"])

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", membershiprole, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("club_id", "user_id", name="uq_membership_club_user"),
    )
    op.create_index("ix_memberships_club_id", "memberships", ["club_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("plan_type", plantype, nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_plans_club_id", "plans", ["club_id"])

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("repetitions", sa.Integer(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("day_label", daylabel, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("plan_id", "position", name="uq_exercises_plan_position"),
    )
    op.create_index("ix_exercises_plan_id", "exercises", ["plan_id"])

    # ---- Plan Assignments (supports user OR group, XOR) ----
    op.create_table(
        "plan_assignments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("role", planassignee_role, nullable=False),  # "coach" | "athlete"
        sa.Column("assigned_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("plan_id", "user_id", name="uq_plan_assignees_plan_user"),
        sa.UniqueConstraint("plan_id", "group_id", name="uq_plan_assignees_plan_group"),
        sa.CheckConstraint(
            "(user_id IS NOT NULL)::int + (group_id IS NOT NULL)::int = 1",
            name="ck_assignment_exactly_one_target",
        ),
    )
    op.create_index("ix_plan_assignments_plan_id", "plan_assignments", ["plan_id"])
    op.create_index("ix_plan_assignments_user_id", "plan_assignments", ["user_id"])
    op.create_index("ix_plan_assignments_group_id", "plan_assignments", ["group_id"])

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=100), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sessions_plan_id_starts_at", "sessions", ["plan_id", "starts_at"])

    # ---- Attendance ----
    op.create_table(
        "attendances",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", attendancestatus, nullable=False, server_default=sa.text("'present'")),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_by_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("session_id", "user_id", name="uq_attendance_session_user"),
    )
    op.create_index("ix_attendance_session_id", "attendances", ["session_id"])
    op.create_index("ix_attendance_user_id", "attendances", ["user_id"])
    op.create_index("ix_attendance_recorded_by_id", "attendances", ["recorded_by_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in reverse dependency order, then enums.
    op.drop_index("ix_attendance_recorded_by_id", table_name="attendances")
    op.drop_index("ix_attendance_user_id", table_name="attendances")
    op.drop_index("ix_attendance_session_id", table_name="attendances")
    op.drop_table("attendances")

    op.drop_index("ix_sessions_plan_id_starts_at", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_plan_assignments_group_id", table_name="plan_assignments")
    op.drop_index("ix_plan_assignments_user_id", table_name="plan_assignments")
    op.drop_index("ix_plan_assignments_plan_id", table_name="plan_assignments")
    op.drop_table("plan_assignments")

    op.drop_index("ix_exercises_plan_id", table_name="exercises")
    op.drop_table("exercises")

    op.drop_index("ix_plans_club_id", table_name="plans")
    op.drop_table("plans")

    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_club_id", table_name="memberships")
    op.drop_table("memberships")

    op.drop_index("ix_group_memberships_user_id", table_name="group_memberships")
    op.drop_index("ix_group_memberships_group_id", table_name="group_memberships")
    op.drop_table("group_memberships")

    op.drop_index("ix_groups_club_id", table_name="groups")
    op.drop_table("groups")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_table("clubs")

    # Drop enums last (guarded).
    bind = op.get_bind()
    for enum_name in ("attendancestatus", "planassignee_role", "daylabel", "plantype", "membershiprole", "userrole"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
