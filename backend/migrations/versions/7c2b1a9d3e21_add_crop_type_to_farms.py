"""add crop_type to farms

Revision ID: 7c2b1a9d3e21
Revises: 0fc8fa641c98
Create Date: 2026-01-10

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '7c2b1a9d3e21'
down_revision: Union[str, Sequence[str], None] = '0fc8fa641c98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    cols = inspector.get_columns(table_name)
    return any(c.get('name') == column_name for c in cols)


def upgrade() -> None:
    """Upgrade schema."""
    # Add crop_type if missing (some dev DBs may already have it)
    if not _has_column('farms', 'crop_type'):
        op.add_column('farms', sa.Column('crop_type', sa.String(length=50), nullable=True))

    # Province exists in the SQLAlchemy model but may not exist in older DBs.
    if not _has_column('farms', 'province'):
        op.add_column('farms', sa.Column('province', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Only drop if present to keep downgrade safe.
    if _has_column('farms', 'crop_type'):
        op.drop_column('farms', 'crop_type')
    # province is older/legacy; do not drop automatically.
