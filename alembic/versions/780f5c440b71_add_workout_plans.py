"""add workout plans

Revision ID: 780f5c440b71
Revises: 5101781ff0b4
Create Date: 2026-01-21 14:24:23.627135

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '780f5c440b71'
down_revision: Union[str, Sequence[str], None] = '5101781ff0b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "workout_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        sa.Column("club_id", sa.Integer(), sa.ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),

        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),

        sa.Column("goal", sa.String(length=120), nullable=True),
        sa.Column("level", sa.String(length=40), nullable=True),
        sa.Column("duration_weeks", sa.Integer(), nullable=True),

        sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),

        # adjust if your TimestampMixin differs
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.UniqueConstraint("club_id", "name", name="uq_workout_plans_club_name"),
    )
    op.create_index("ix_workout_plans_club_id", "workout_plans", ["club_id"])
    op.create_index("ix_workout_plans_created_by_id", "workout_plans", ["created_by_id"])

    op.create_table(
        "workout_plan_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),

        sa.Column("week_number", sa.Integer(), nullable=True),
        # IMPORTANT: reuse your existing enum name if it exists. If unsure, see note below.
        sa.Column(
            "day_label",
            postgresql.ENUM(
                "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                name="daylabel",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),

        sa.Column("title", sa.String(length=120), nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.UniqueConstraint(
            "plan_id", "week_number", "day_label", "order_index",
            name="uq_workout_plan_items_plan_week_day_order",
        ),
        sa.CheckConstraint("order_index >= 0", name="ck_workout_plan_items_order_index_nonneg"),
        sa.CheckConstraint("week_number IS NULL OR week_number >= 1", name="ck_workout_plan_items_week_number_ge_1"),
    )
    op.create_index("ix_workout_plan_items_plan_id", "workout_plan_items", ["plan_id"])

    op.create_table(
        "workout_plan_exercises",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),

        sa.Column("item_id", sa.Integer(), sa.ForeignKey("workout_plan_items.id", ondelete="CASCADE"), nullable=False),

        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),

        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("repetitions", sa.Integer(), nullable=True),

        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("tempo", sa.String(length=32), nullable=True),
        sa.Column("weight_kg", sa.Integer(), nullable=True),

        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),

        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),

        sa.UniqueConstraint("item_id", "position", name="uq_workout_plan_exercises_item_position"),
        sa.CheckConstraint("position >= 0", name="ck_workout_plan_exercises_position_nonneg"),
    )
    op.create_index("ix_workout_plan_exercises_item_id", "workout_plan_exercises", ["item_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_plan_exercises_item_id", table_name="workout_plan_exercises")
    op.drop_table("workout_plan_exercises")

    op.drop_index("ix_workout_plan_items_plan_id", table_name="workout_plan_items")
    op.drop_table("workout_plan_items")

    op.drop_index("ix_workout_plans_created_by_id", table_name="workout_plans")
    op.drop_index("ix_workout_plans_club_id", table_name="workout_plans")
    op.drop_table("workout_plans")

