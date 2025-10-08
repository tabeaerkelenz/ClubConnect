"""merge heads (64df2f933d6d + be20a8201a71)

Revision ID: 9e986c723aad
Revises: 64df2f933d6d, be20a8201a71
Create Date: 2025-10-08 13:52:18.565021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e986c723aad'
down_revision: Union[str, Sequence[str], None] = ('64df2f933d6d', 'be20a8201a71')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
