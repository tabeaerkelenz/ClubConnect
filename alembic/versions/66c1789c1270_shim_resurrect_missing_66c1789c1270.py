"""shim: resurrect missing 66c1789c1270

Revision ID: 66c1789c1270
Revises: 9e986c723aad
Create Date: 2025-10-08 14:09:09.256882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66c1789c1270'
down_revision: Union[str, Sequence[str], None] = 'ae83e0698d80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
