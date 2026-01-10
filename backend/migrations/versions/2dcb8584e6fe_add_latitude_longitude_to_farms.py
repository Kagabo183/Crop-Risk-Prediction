"""add_latitude_longitude_to_farms

Revision ID: 2dcb8584e6fe
Revises: advanced_intelligence
Create Date: 2026-01-01 17:51:47.165467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dcb8584e6fe'
down_revision: Union[str, Sequence[str], None] = 'advanced_intelligence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('farms', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('farms', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('farms', 'longitude')
    op.drop_column('farms', 'latitude')
