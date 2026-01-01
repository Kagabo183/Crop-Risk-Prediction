"""add prediction model

Revision ID: 00d45d04a01d
Revises: 9f3ed52b5be6
Create Date: 2025-12-30 13:14:26.258562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00d45d04a01d'
down_revision: Union[str, Sequence[str], None] = '9f3ed52b5be6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('farm_id', sa.Integer, nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('risk_score', sa.Float, nullable=False),
        sa.Column('yield_loss_percent', sa.Float, nullable=True),
        sa.Column('disease_risk_level', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('predictions')
