"""add prediction model

Revision ID: 9f3ed52b5be6
Revises: 04fb0d8deb40
Create Date: 2025-12-30 13:13:38.202970

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f3ed52b5be6'
down_revision: Union[str, Sequence[str], None] = '04fb0d8deb40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
