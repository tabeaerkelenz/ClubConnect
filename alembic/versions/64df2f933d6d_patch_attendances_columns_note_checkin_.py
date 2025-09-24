"""patch attendances columns (note + checkin/checkout + recorded_by_id)

Revision ID: 64df2f933d6d
Revises: 37cf0d7a1cf5
Create Date: 2025-09-25 00:57:38.972096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64df2f933d6d'
down_revision: Union[str, Sequence[str], None] = '37cf0d7a1cf5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- add missing columns (safe if already present) ---
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS recorded_by_id INTEGER")
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS checked_in_at  TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS checked_out_at TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS note TEXT NULL")

    # --- indexes (safe if already present) ---
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_recorded_by_id ON attendances (recorded_by_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_checked_in_at  ON attendances (checked_in_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_checked_out_at ON attendances (checked_out_at)")

    # --- FK recorded_by_id -> users(id) (safe if already present) ---
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_attendances_recorded_by_id_users'
          AND conrelid = 'attendances'::regclass
      ) THEN
        ALTER TABLE attendances
          ADD CONSTRAINT fk_attendances_recorded_by_id_users
          FOREIGN KEY (recorded_by_id) REFERENCES users(id) ON DELETE SET NULL;
      END IF;
    END$$;
    """)

def downgrade() -> None:
    op.execute("ALTER TABLE attendances DROP CONSTRAINT IF EXISTS fk_attendances_recorded_by_id_users")
    op.execute("DROP INDEX IF EXISTS ix_attendance_checked_out_at")
    op.execute("DROP INDEX IF EXISTS ix_attendance_checked_in_at")
    op.execute("DROP INDEX IF EXISTS ix_attendance_recorded_by_id")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS note")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS checked_out_at")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS checked_in_at")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS recorded_by_id")