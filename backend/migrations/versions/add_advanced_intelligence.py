"""add advanced intelligence fields to predictions

Revision ID: advanced_intelligence
Revises: b3e2fdc4721c
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'advanced_intelligence'
down_revision = 'b3e2fdc4721c'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to predictions table
    op.add_column('predictions', sa.Column('time_to_impact', sa.String(), nullable=True))
    op.add_column('predictions', sa.Column('confidence_level', sa.String(), nullable=True))
    op.add_column('predictions', sa.Column('confidence_score', sa.Float(), nullable=True))
    op.add_column('predictions', sa.Column('risk_drivers', sa.JSON(), nullable=True))
    op.add_column('predictions', sa.Column('risk_explanation', sa.Text(), nullable=True))
    op.add_column('predictions', sa.Column('recommendations', sa.JSON(), nullable=True))
    op.add_column('predictions', sa.Column('impact_metrics', sa.JSON(), nullable=True))


def downgrade():
    # Remove new columns
    op.drop_column('predictions', 'impact_metrics')
    op.drop_column('predictions', 'recommendations')
    op.drop_column('predictions', 'risk_explanation')
    op.drop_column('predictions', 'risk_drivers')
    op.drop_column('predictions', 'confidence_score')
    op.drop_column('predictions', 'confidence_level')
    op.drop_column('predictions', 'time_to_impact')
