"""merge heads

Revision ID: 862f2cffa774
Revises: 66c1789c1270, 9e986c723aad
Create Date: 2025-10-08 14:14:37.453121

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '862f2cffa774'
down_revision: Union[str, Sequence[str], None] = ('66c1789c1270', '9e986c723aad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
