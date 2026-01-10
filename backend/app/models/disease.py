"""
Disease models for pathogen-specific crop disease tracking and prediction
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class Disease(Base):
    """Master disease catalog with pathogen information"""
    __tablename__ = "diseases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # e.g., "Late Blight"
    scientific_name = Column(String, nullable=True)  # e.g., "Phytophthora infestans"
    pathogen_type = Column(String, nullable=False)  # "fungal", "bacterial", "viral", "nematode"
    
    # Affected crops
    primary_crops = Column(JSON, nullable=True)  # ["potato", "tomato"]
    
    # Environmental thresholds from research
    optimal_temp_min = Column(Float, nullable=True)
    optimal_temp_max = Column(Float, nullable=True)
    optimal_humidity_min = Column(Float, nullable=True)
    required_leaf_wetness_hours = Column(Float, nullable=True)
    
    # Disease characteristics
    incubation_period_days = Column(Integer, nullable=True)  # Time from infection to symptoms
    severity_potential = Column(String, nullable=True)  # "low", "moderate", "high", "severe"
    spread_rate = Column(String, nullable=True)  # "slow", "moderate", "fast"
    
    # Management information
    symptoms = Column(Text, nullable=True)
    management_practices = Column(JSON, nullable=True)  # List of IPM practices
    chemical_controls = Column(JSON, nullable=True)  # Available fungicides/bactericides
    
    # Research references
    research_source = Column(String, nullable=True)  # University/research institution
    model_type = Column(String, nullable=True)  # "statistical", "mechanistic", "machine_learning"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predictions = relationship("DiseasePrediction", back_populates="disease")


class DiseasePrediction(Base):
    """Disease-specific predictions for farms"""
    __tablename__ = "disease_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)
    
    # Prediction metadata
    predicted_at = Column(DateTime, default=datetime.utcnow)
    prediction_date = Column(Date, nullable=False)  # Date for which prediction is made
    forecast_horizon = Column(String, nullable=False)  # "current", "1-day", "3-day", "7-day", "14-day"
    
    # Risk assessment
    risk_score = Column(Float, nullable=False)  # 0-100
    risk_level = Column(String, nullable=False)  # "low", "moderate", "high", "severe"
    infection_probability = Column(Float, nullable=True)  # 0-1 probability
    
    # Disease development stage
    disease_stage = Column(String, nullable=True)  # "pre-infection", "infection", "incubation", "active"
    days_to_symptom_onset = Column(Integer, nullable=True)  # Estimated days until visible symptoms
    
    # Contributing factors
    weather_risk_score = Column(Float, nullable=True)  # Weather conduciveness (0-100)
    host_susceptibility_score = Column(Float, nullable=True)  # Crop vulnerability (0-100)
    pathogen_pressure_score = Column(Float, nullable=True)  # Local disease pressure (0-100)
    
    # Detailed risk factors
    risk_factors = Column(JSON, nullable=True)  # {"temp": 0.8, "humidity": 0.9, "leaf_wetness": 0.85}
    weather_conditions = Column(JSON, nullable=True)  # Current/forecasted weather
    
    # Model outputs
    model_version = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)  # Model confidence (0-100)
    
    # Recommendations
    action_threshold_reached = Column(Boolean, default=False)  # Should farmer act?
    recommended_actions = Column(JSON, nullable=True)  # List of IPM actions
    treatment_window = Column(String, nullable=True)  # "immediate", "within 24h", "within 3 days"
    
    # Economic impact
    estimated_yield_loss_pct = Column(Float, nullable=True)  # % yield loss if untreated
    economic_risk = Column(String, nullable=True)  # "low", "moderate", "high"
    
    # Relationships
    farm = relationship("Farm")
    disease = relationship("Disease", back_populates="predictions")


class DiseaseObservation(Base):
    """Ground-truth disease observations from scouts/farmers"""
    __tablename__ = "disease_observations"
    
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=True)
    
    # Observation details
    observed_at = Column(DateTime, default=datetime.utcnow)
    observation_date = Column(Date, nullable=False)
    observer_name = Column(String, nullable=True)
    
    # Disease details
    disease_present = Column(Boolean, nullable=False)
    disease_severity = Column(String, nullable=True)  # "trace", "low", "moderate", "high", "severe"
    incidence_pct = Column(Float, nullable=True)  # % of plants affected
    severity_rating = Column(Float, nullable=True)  # 0-10 scale
    
    # Spatial information
    location_description = Column(String, nullable=True)  # "north field", "section B"
    gps_coordinates = Column(JSON, nullable=True)  # {"lat": x, "lon": y}
    
    # Supporting data
    symptoms_observed = Column(Text, nullable=True)
    photos = Column(JSON, nullable=True)  # URLs to photos
    notes = Column(Text, nullable=True)
    
    # Validation
    confirmed_by_expert = Column(Boolean, default=False)
    lab_diagnosis = Column(String, nullable=True)
    
    # Relationships
    farm = relationship("Farm")


class DiseaseModelConfig(Base):
    """Configuration for pathogen-specific prediction models"""
    __tablename__ = "disease_model_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey("diseases.id"), nullable=False)
    
    # Model configuration
    model_name = Column(String, nullable=False)  # "Late Blight Smith Period", "Septoria Leaf Spot TOM-CAST"
    model_type = Column(String, nullable=False)  # "rule_based", "statistical", "machine_learning"
    is_active = Column(Boolean, default=True)
    
    # Thresholds and parameters
    risk_thresholds = Column(JSON, nullable=False)  # {"low": 30, "moderate": 50, "high": 70, "severe": 85}
    model_parameters = Column(JSON, nullable=True)  # Model-specific params
    
    # Weather requirements
    temp_weight = Column(Float, default=0.3)
    humidity_weight = Column(Float, default=0.3)
    rainfall_weight = Column(Float, default=0.2)
    leaf_wetness_weight = Column(Float, default=0.2)
    
    # Forecast configuration
    max_forecast_days = Column(Integer, default=7)
    min_confidence_threshold = Column(Float, default=0.6)
    
    # University/research backing
    research_institution = Column(String, nullable=True)
    validation_studies = Column(JSON, nullable=True)  # References to validation papers
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    disease = relationship("Disease")


class WeatherForecast(Base):
    """Short-term weather forecasts for disease prediction"""
    __tablename__ = "weather_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)  # "Lat:x,Lon:y" or region name
    
    # Forecast metadata
    forecast_date = Column(Date, nullable=False)  # Date of forecast creation
    valid_date = Column(Date, nullable=False)  # Date for which forecast is valid
    forecast_horizon_hours = Column(Integer, nullable=False)  # Hours ahead
    
    # Weather variables
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    temperature_mean = Column(Float, nullable=True)
    
    humidity_min = Column(Float, nullable=True)
    humidity_max = Column(Float, nullable=True)
    humidity_mean = Column(Float, nullable=True)
    
    rainfall_total = Column(Float, nullable=True)  # mm
    rainfall_probability = Column(Float, nullable=True)  # 0-1
    
    wind_speed = Column(Float, nullable=True)
    dewpoint = Column(Float, nullable=True)
    
    # Disease-relevant derived variables
    leaf_wetness_hours = Column(Float, nullable=True)  # Estimated hours of leaf wetness
    evapotranspiration = Column(Float, nullable=True)
    
    # Forecast source
    source = Column(String, nullable=False)  # "NOAA", "ERA5", "IBM_EIS", "INTEGRATED"
    confidence = Column(Float, nullable=True)  # Forecast confidence
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    extra_metadata = Column(JSON, nullable=True)
