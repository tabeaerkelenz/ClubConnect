from alembic import op
import sqlalchemy as sa

revision = "f2c63d4b5530"
down_revision = "8bdceb080455"
branch_labels = None
depends_on = None

def upgrade() -> None:
    # --- groups table ---
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("club_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.UniqueConstraint("club_id", "name", name="uq_group_name_per_club"),
    )
    # index (guarded)
    op.execute("CREATE INDEX IF NOT EXISTS ix_groups_club_id ON groups (club_id)")

    # --- group_memberships table ---
    op.create_table(
        "group_memberships",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id", "user_id"),
    )
    # indexes (guarded)
    op.execute("CREATE INDEX IF NOT EXISTS ix_group_memberships_group_id ON group_memberships (group_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_group_memberships_user_id  ON group_memberships (user_id)")

    # --- plan_assignments.group_id (column + FK + index + unique) ---
    # add column if missing
    op.execute("ALTER TABLE plan_assignments ADD COLUMN IF NOT EXISTS group_id INTEGER")

    # FK (guarded by name)
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_plan_assignments_group_id_groups'
          AND conrelid = 'plan_assignments'::regclass
      ) THEN
        ALTER TABLE plan_assignments
          ADD CONSTRAINT fk_plan_assignments_group_id_groups
          FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE;
      END IF;
    END$$;
    """)

    # index on group_id (guarded)
    op.execute("CREATE INDEX IF NOT EXISTS ix_plan_assignments_group_id ON plan_assignments (group_id)")

    # unique (plan_id, group_id) (guarded by name)
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_plan_assignees_plan_group'
          AND conrelid = 'plan_assignments'::regclass
      ) THEN
        ALTER TABLE plan_assignments
          ADD CONSTRAINT uq_plan_assignees_plan_group
          UNIQUE (plan_id, group_id);
      END IF;
    END$$;
    """)

    # XOR check constraint (drop any old name; create if missing)
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_plan_assignment_one_target'
          AND conrelid = 'plan_assignments'::regclass
      ) THEN
        ALTER TABLE plan_assignments DROP CONSTRAINT ck_plan_assignment_one_target;
      END IF;

      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'ck_assignment_exactly_one_target'
          AND conrelid = 'plan_assignments'::regclass
      ) THEN
        ALTER TABLE plan_assignments
          ADD CONSTRAINT ck_assignment_exactly_one_target
          CHECK ( ((user_id IS NOT NULL)::int + (group_id IS NOT NULL)::int) = 1 );
      END IF;
    END$$;
    """)

def downgrade() -> None:
    # reverse in safe order
    op.execute("ALTER TABLE plan_assignments DROP CONSTRAINT IF EXISTS ck_assignment_exactly_one_target")
    op.execute("ALTER TABLE plan_assignments DROP CONSTRAINT IF EXISTS uq_plan_assignees_plan_group")
    op.execute("DROP INDEX IF EXISTS ix_plan_assignments_group_id")
    op.execute("ALTER TABLE plan_assignments DROP CONSTRAINT IF EXISTS fk_plan_assignments_group_id_groups")
    op.execute("ALTER TABLE plan_assignments DROP COLUMN IF EXISTS group_id")

    op.execute("DROP INDEX IF EXISTS ix_group_memberships_user_id")
    op.execute("DROP INDEX IF EXISTS ix_group_memberships_group_id")
    op.drop_table("group_memberships")

    op.execute("DROP INDEX IF EXISTS ix_groups_club_id")
    op.drop_table("groups")
