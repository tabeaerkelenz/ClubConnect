"""add checkin/checkout timestamps to attendances

Revision ID: 37cf0d7a1cf5
Revises: ae83e0698d80
Create Date: 2025-09-25 00:34:51.539356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37cf0d7a1cf5'
down_revision: Union[str, Sequence[str], None] = 'ae83e0698d80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS checked_in_at  TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS checked_out_at TIMESTAMPTZ NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_checked_in_at  ON attendances (checked_in_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_checked_out_at ON attendances (checked_out_at)")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_attendance_checked_out_at")
    op.execute("DROP INDEX IF EXISTS ix_attendance_checked_in_at")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS checked_out_at")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS checked_in_at")