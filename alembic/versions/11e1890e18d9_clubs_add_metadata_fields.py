"""clubs: add metadata fields

Revision ID: 11e1890e18d9
Revises: 64df2f933d6d
Create Date: 2025-10-19 21:16:45.053054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11e1890e18d9'
down_revision: Union[str, Sequence[str], None] = '64df2f933d6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("clubs", sa.Column("country", sa.String(length=4), nullable=True))
    op.add_column("clubs", sa.Column("city", sa.String(length=128), nullable=True))
    op.add_column("clubs", sa.Column("sport", sa.String(length=100), nullable=True))
    op.add_column("clubs", sa.Column("founded_year", sa.Integer(), nullable=True))
    op.add_column("clubs", sa.Column("description", sa.Text(), nullable=True))

    # Functional indexes (use raw SQL for portability w/ Alembic)
    op.execute("CREATE INDEX IF NOT EXISTS ix_clubs_city_lower ON clubs (LOWER(city))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clubs_name_lower ON clubs (LOWER(name))")
    op.execute("CREATE INDEX IF NOT EXISTS ix_clubs_sport_lower ON clubs (LOWER(sport))")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_clubs_sport_lower")
    op.execute("DROP INDEX IF EXISTS ix_clubs_name_lower")
    op.execute("DROP INDEX IF EXISTS ix_clubs_city_lower")

    op.drop_column("clubs", "description")
    op.drop_column("clubs", "founded_year")
    op.drop_column("clubs", "sport")
    op.drop_column("clubs", "city")
    op.drop_column("clubs", "country")