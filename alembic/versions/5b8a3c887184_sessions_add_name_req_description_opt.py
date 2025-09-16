"""sessions: add name (req) & description (opt)

Revision ID: 5b8a3c887184
Revises: 002735126b5e
Create Date: 2025-09-16 13:39:52.210018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b8a3c887184'
down_revision: Union[str, Sequence[str], None] = '002735126b5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) Add columns (temporary default on name for backfill)
    op.add_column(
        "sessions",
        sa.Column("name", sa.String(length=100), nullable=False, server_default=sa.text("'Session'")),
    )
    op.add_column(
        "sessions",
        sa.Column("description", sa.Text(), nullable=True),
    )

    # 2) Defensive backfill (covers odd states)
    op.execute("UPDATE sessions SET name = 'Session' WHERE name IS NULL;")

    # 3) Drop the default so future inserts must supply name
    op.alter_column("sessions", "name", server_default=None)

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("sessions", "description")
    op.drop_column("sessions", "name")
