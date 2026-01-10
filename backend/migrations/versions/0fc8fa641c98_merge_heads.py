"""merge_heads

Revision ID: 0fc8fa641c98
Revises: 2dcb8584e6fe, disease_prediction_v1
Create Date: 2026-01-03 15:43:35.171638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0fc8fa641c98'
down_revision: Union[str, Sequence[str], None] = ('2dcb8584e6fe', 'disease_prediction_v1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
