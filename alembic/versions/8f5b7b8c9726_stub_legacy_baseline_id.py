"""stub: legacy baseline id

Revision ID: 8f5b7b8c9726
Revises: 8bdceb080455
Create Date: 2025-09-24 15:52:47.224263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f5b7b8c9726'
down_revision: Union[str, Sequence[str], None] = '8bdceb080455'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
