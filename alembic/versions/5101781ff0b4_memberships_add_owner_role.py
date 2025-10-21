"""memberships: add owner role

Revision ID: 5101781ff0b4
Revises: 11e1890e18d9
Create Date: 2025-10-20 17:21:10.566285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5101781ff0b4'
down_revision: Union[str, Sequence[str], None] = '11e1890e18d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_TYPE = "membershiprole"
NEW_TYPE = "membershiprole_new"



def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"CREATE TYPE {NEW_TYPE} AS ENUM ('member','coach','owner')")

    # switch ALL enum-typed columns to the new type
    op.execute(f"ALTER TABLE memberships        ALTER COLUMN role TYPE {NEW_TYPE} USING role::text::{NEW_TYPE}")
    op.execute(f"ALTER TABLE group_memberships  ALTER COLUMN role TYPE {NEW_TYPE} USING role::text::{NEW_TYPE}")

    op.execute(f"DROP TYPE {OLD_TYPE}")
    op.execute(f"ALTER TYPE {NEW_TYPE} RENAME TO {OLD_TYPE}")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"CREATE TYPE {NEW_TYPE} AS ENUM ('member','coach')")

    # map 'owner' to a fallback on downgrade
    op.execute(f"""
            ALTER TABLE memberships
            ALTER COLUMN role TYPE {NEW_TYPE}
            USING CASE
                WHEN role::text = 'owner' THEN 'coach'
                ELSE role::text
            END::{NEW_TYPE}
        """)
    op.execute(f"""
            ALTER TABLE group_memberships
            ALTER COLUMN role TYPE {NEW_TYPE}
            USING CASE
                WHEN role::text = 'owner' THEN 'coach'
                ELSE role::text
            END::{NEW_TYPE}
        """)

    op.execute(f"DROP TYPE {OLD_TYPE}")
    op.execute(f"ALTER TYPE {NEW_TYPE} RENAME TO {OLD_TYPE}")