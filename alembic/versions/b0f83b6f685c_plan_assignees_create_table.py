"""plan_assignees: create table

Revision ID: b0f83b6f685c
Revises: 5b8a3c887184
Create Date: 2025-09-16 19:57:30.155649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0f83b6f685c'
down_revision: Union[str, Sequence[str], None] = '5b8a3c887184'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Dedicated ENUM for assigned role (coach|athlete)
role_enum_name = "planassignee_role"

def upgrade() -> None:
    """Upgrade schema."""

    # IMPORTANT: prevent SQLAlchemy from trying to CREATE TYPE again
    enum_col = sa.Enum("coach", "athlete", name=role_enum_name, create_type=False)

    # 2) Create table
    op.create_table(
        "plan_assignments",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("role", enum_col, nullable=False),
        sa.Column("assigned_by_id", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("plan_id", "user_id", name="uq_plan_assignments_plan_user"),
    )

    # 3) Helpful indexes
    op.create_index("ix_plan_assignments_plan_id", "plan_assignments", ["plan_id"])
    op.create_index("ix_plan_assignments_user_id", "plan_assignments", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes then table, then ENUM
    op.drop_index("ix_plan_assignments_user_id", table_name="plan_assignments")
    op.drop_index("ix_plan_assignments_plan_id", table_name="plan_assignments")
    op.drop_table("plan_assignments")

    op.execute("DROP TYPE IF EXISTS planassignee_role;")
