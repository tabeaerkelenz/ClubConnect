from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ae83e0698d80"
down_revision = "f2c63d4b5530"  # <-- adjust if your head is different
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1) add column if missing
    op.execute("ALTER TABLE attendances ADD COLUMN IF NOT EXISTS recorded_by_id INTEGER")

    # 2) create index if missing
    op.execute("CREATE INDEX IF NOT EXISTS ix_attendance_recorded_by_id ON attendances (recorded_by_id)")

    # 3) add FK if missing
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
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
    op.execute("DROP INDEX IF EXISTS ix_attendance_recorded_by_id")
    op.execute("ALTER TABLE attendances DROP COLUMN IF EXISTS recorded_by_id")
