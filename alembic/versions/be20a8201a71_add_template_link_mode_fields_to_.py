"""add template/link_mode fields to session and exercises

Revision ID: be20a8201a71
Revises: 64df2f933d6d
Create Date: 2025-10-08 12:50:37.399082

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'be20a8201a71'
down_revision: Union[str, Sequence[str], None] = 'ae83e0698d80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Ensure shared ENUM exists
    linkmode_enum = postgresql.ENUM("snapshot", "linked", name="linkmode", create_type=False)
    linkmode_enum.create(bind, checkfirst=True)

    # --- sessions ---
    op.add_column(
        "sessions",
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("sessions", sa.Column("template_id", sa.Integer(), nullable=True))
    op.add_column(
        "sessions",
        sa.Column("link_mode", sa.Enum("snapshot", "linked", name="linkmode"), nullable=False,
                  server_default=sa.text("'snapshot'")),
    )
    op.add_column("sessions", sa.Column("template_version_used", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_sessions_template_id_sessions",
        source_table="sessions",
        referent_table="sessions",
        local_cols=["template_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    # --- exercises ---
    op.add_column(
        "exercises",
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("exercises", sa.Column("template_id", sa.Integer(), nullable=True))
    op.add_column(
        "exercises",
        sa.Column("link_mode", sa.Enum("snapshot", "linked", name="linkmode"), nullable=False,
                  server_default=sa.text("'snapshot'")),
    )
    op.add_column("exercises", sa.Column("template_version_used", sa.Integer(), nullable=True))

    op.create_foreign_key(
        "fk_exercises_template_id_exercises",
        source_table="exercises",
        referent_table="exercises",
        local_cols=["template_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    # Optional: drop server defaults for future inserts (keep values applied to existing rows)
    op.alter_column("sessions", "is_template", server_default=None)
    op.alter_column("sessions", "link_mode", server_default=None)
    op.alter_column("exercises", "is_template", server_default=None)
    op.alter_column("exercises", "link_mode", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    op.drop_constraint("fk_exercises_template_id_exercises", "exercises", type_="foreignkey")
    op.drop_constraint("fk_sessions_template_id_sessions", "sessions", type_="foreignkey")

    op.drop_column("exercises", "template_version_used")
    op.drop_column("exercises", "link_mode")
    op.drop_column("exercises", "template_id")
    op.drop_column("exercises", "is_template")

    op.drop_column("sessions", "template_version_used")
    op.drop_column("sessions", "link_mode")
    op.drop_column("sessions", "template_id")
    op.drop_column("sessions", "is_template")

    linkmode_enum = postgresql.ENUM("snapshot", "linked", name="linkmode", create_type=False)
    linkmode_enum.drop(bind, checkfirst=True)
