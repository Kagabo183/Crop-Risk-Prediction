"""Add disease prediction models and weather forecasts

Revision ID: disease_prediction_v1
Revises: latest
Create Date: 2026-01-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'disease_prediction_v1'
down_revision = None  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Create diseases table
    op.create_table(
        'diseases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('scientific_name', sa.String(), nullable=True),
        sa.Column('pathogen_type', sa.String(), nullable=False),
        sa.Column('primary_crops', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('optimal_temp_min', sa.Float(), nullable=True),
        sa.Column('optimal_temp_max', sa.Float(), nullable=True),
        sa.Column('optimal_humidity_min', sa.Float(), nullable=True),
        sa.Column('required_leaf_wetness_hours', sa.Float(), nullable=True),
        sa.Column('incubation_period_days', sa.Integer(), nullable=True),
        sa.Column('severity_potential', sa.String(), nullable=True),
        sa.Column('spread_rate', sa.String(), nullable=True),
        sa.Column('symptoms', sa.Text(), nullable=True),
        sa.Column('management_practices', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('chemical_controls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('research_source', sa.String(), nullable=True),
        sa.Column('model_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_diseases_id'), 'diseases', ['id'], unique=False)
    
    # Create disease_predictions table
    op.create_table(
        'disease_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=False),
        sa.Column('predicted_at', sa.DateTime(), nullable=True),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('forecast_horizon', sa.String(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(), nullable=False),
        sa.Column('infection_probability', sa.Float(), nullable=True),
        sa.Column('disease_stage', sa.String(), nullable=True),
        sa.Column('days_to_symptom_onset', sa.Integer(), nullable=True),
        sa.Column('weather_risk_score', sa.Float(), nullable=True),
        sa.Column('host_susceptibility_score', sa.Float(), nullable=True),
        sa.Column('pathogen_pressure_score', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('weather_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('model_version', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('action_threshold_reached', sa.Boolean(), nullable=True),
        sa.Column('recommended_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('treatment_window', sa.String(), nullable=True),
        sa.Column('estimated_yield_loss_pct', sa.Float(), nullable=True),
        sa.Column('economic_risk', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disease_predictions_id'), 'disease_predictions', ['id'], unique=False)
    
    # Create disease_observations table
    op.create_table(
        'disease_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('farm_id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=True),
        sa.Column('observed_at', sa.DateTime(), nullable=True),
        sa.Column('observation_date', sa.Date(), nullable=False),
        sa.Column('observer_name', sa.String(), nullable=True),
        sa.Column('disease_present', sa.Boolean(), nullable=False),
        sa.Column('disease_severity', sa.String(), nullable=True),
        sa.Column('incidence_pct', sa.Float(), nullable=True),
        sa.Column('severity_rating', sa.Float(), nullable=True),
        sa.Column('location_description', sa.String(), nullable=True),
        sa.Column('gps_coordinates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('symptoms_observed', sa.Text(), nullable=True),
        sa.Column('photos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('confirmed_by_expert', sa.Boolean(), nullable=True),
        sa.Column('lab_diagnosis', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ),
        sa.ForeignKeyConstraint(['farm_id'], ['farms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disease_observations_id'), 'disease_observations', ['id'], unique=False)
    
    # Create disease_model_configs table
    op.create_table(
        'disease_model_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('disease_id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('model_type', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('risk_thresholds', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('model_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('temp_weight', sa.Float(), nullable=True),
        sa.Column('humidity_weight', sa.Float(), nullable=True),
        sa.Column('rainfall_weight', sa.Float(), nullable=True),
        sa.Column('leaf_wetness_weight', sa.Float(), nullable=True),
        sa.Column('max_forecast_days', sa.Integer(), nullable=True),
        sa.Column('min_confidence_threshold', sa.Float(), nullable=True),
        sa.Column('research_institution', sa.String(), nullable=True),
        sa.Column('validation_studies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disease_model_configs_id'), 'disease_model_configs', ['id'], unique=False)
    
    # Create weather_forecasts table
    op.create_table(
        'weather_forecasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('valid_date', sa.Date(), nullable=False),
        sa.Column('forecast_horizon_hours', sa.Integer(), nullable=False),
        sa.Column('temperature_min', sa.Float(), nullable=True),
        sa.Column('temperature_max', sa.Float(), nullable=True),
        sa.Column('temperature_mean', sa.Float(), nullable=True),
        sa.Column('humidity_min', sa.Float(), nullable=True),
        sa.Column('humidity_max', sa.Float(), nullable=True),
        sa.Column('humidity_mean', sa.Float(), nullable=True),
        sa.Column('rainfall_total', sa.Float(), nullable=True),
        sa.Column('rainfall_probability', sa.Float(), nullable=True),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('dewpoint', sa.Float(), nullable=True),
        sa.Column('leaf_wetness_hours', sa.Float(), nullable=True),
        sa.Column('evapotranspiration', sa.Float(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_forecasts_id'), 'weather_forecasts', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_weather_forecasts_id'), table_name='weather_forecasts')
    op.drop_table('weather_forecasts')
    
    op.drop_index(op.f('ix_disease_model_configs_id'), table_name='disease_model_configs')
    op.drop_table('disease_model_configs')
    
    op.drop_index(op.f('ix_disease_observations_id'), table_name='disease_observations')
    op.drop_table('disease_observations')
    
    op.drop_index(op.f('ix_disease_predictions_id'), table_name='disease_predictions')
    op.drop_table('disease_predictions')
    
    op.drop_index(op.f('ix_diseases_id'), table_name='diseases')
    op.drop_table('diseases')
