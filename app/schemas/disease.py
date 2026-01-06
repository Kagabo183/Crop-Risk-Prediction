"""
Pydantic schemas for disease predictions and forecasts
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class DiseaseType(str, Enum):
    """Pathogen types"""
    fungal = "fungal"
    bacterial = "bacterial"
    viral = "viral"
    nematode = "nematode"


class RiskLevel(str, Enum):
    """Risk level categories"""
    low = "low"
    moderate = "moderate"
    high = "high"
    severe = "severe"


class ForecastHorizon(str, Enum):
    """Forecast time horizons"""
    current = "current"
    one_day = "1-day"
    three_day = "3-day"
    seven_day = "7-day"
    fourteen_day = "14-day"


class DiseaseBase(BaseModel):
    """Base disease information"""
    name: str
    scientific_name: Optional[str] = None
    pathogen_type: DiseaseType
    primary_crops: Optional[List[str]] = None


class DiseaseCreate(DiseaseBase):
    """Create new disease entry"""
    optimal_temp_min: Optional[float] = None
    optimal_temp_max: Optional[float] = None
    optimal_humidity_min: Optional[float] = None
    required_leaf_wetness_hours: Optional[float] = None
    incubation_period_days: Optional[int] = None
    severity_potential: Optional[str] = None
    research_source: Optional[str] = None
    model_type: Optional[str] = None


class Disease(DiseaseBase):
    """Disease response"""
    id: int
    optimal_temp_min: Optional[float] = None
    optimal_temp_max: Optional[float] = None
    optimal_humidity_min: Optional[float] = None
    required_leaf_wetness_hours: Optional[float] = None
    incubation_period_days: Optional[int] = None
    severity_potential: Optional[str] = None
    symptoms: Optional[str] = None
    management_practices: Optional[List[str]] = None
    research_source: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiseasePredictionRequest(BaseModel):
    """Request for disease prediction"""
    farm_id: int
    disease_name: str = Field(..., description="Disease name (e.g., 'Late Blight', 'Septoria Leaf Spot')")
    crop_type: Optional[str] = Field(None, description="Crop type (e.g., 'potato', 'tomato')")
    forecast_days: int = Field(7, ge=1, le=14, description="Number of days to forecast (1-14)")
    include_recommendations: bool = Field(True, description="Include management recommendations")


class DiseasePredictionBase(BaseModel):
    """Base disease prediction"""
    farm_id: int
    disease_id: int
    prediction_date: date
    forecast_horizon: str
    risk_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    infection_probability: Optional[float] = Field(None, ge=0, le=1)


class DiseasePredictionCreate(DiseasePredictionBase):
    """Create disease prediction"""
    disease_stage: Optional[str] = None
    days_to_symptom_onset: Optional[int] = None
    weather_risk_score: Optional[float] = None
    risk_factors: Optional[Dict[str, Any]] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    action_threshold_reached: bool = False
    recommended_actions: Optional[List[str]] = None
    treatment_window: Optional[str] = None
    estimated_yield_loss_pct: Optional[float] = None


class DiseasePrediction(DiseasePredictionBase):
    """Disease prediction response"""
    id: int
    predicted_at: datetime
    disease_stage: Optional[str] = None
    days_to_symptom_onset: Optional[int] = None
    weather_risk_score: Optional[float] = None
    host_susceptibility_score: Optional[float] = None
    pathogen_pressure_score: Optional[float] = None
    risk_factors: Optional[Dict[str, Any]] = None
    weather_conditions: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    confidence_score: Optional[float] = None
    action_threshold_reached: bool
    recommended_actions: Optional[List[str]] = None
    treatment_window: Optional[str] = None
    estimated_yield_loss_pct: Optional[float] = None
    economic_risk: Optional[str] = None
    
    class Config:
        from_attributes = True


class DailyForecast(BaseModel):
    """Daily disease risk forecast"""
    date: date
    day_offset: int
    forecast_horizon: str
    disease_name: str
    risk_score: float
    risk_level: RiskLevel
    weather: Dict[str, Any]
    confidence: float
    actionable: bool


class WeeklyForecastSummary(BaseModel):
    """Weekly disease forecast summary"""
    disease_name: str
    forecast_period: str
    start_date: date
    end_date: date
    weekly_risk_level: RiskLevel
    average_risk_score: float
    peak_risk_score: float
    peak_risk_day: date
    critical_action_days: int
    critical_dates: List[date]
    daily_forecasts: List[DailyForecast]
    recommended_strategy: str


class DiseasePredictionResponse(BaseModel):
    """Complete disease prediction response"""
    prediction: DiseasePrediction
    disease_info: Disease
    current_risk: Dict[str, Any]
    forecast: Optional[WeeklyForecastSummary] = None


class DiseaseObservationCreate(BaseModel):
    """Create disease observation"""
    farm_id: int
    disease_id: Optional[int] = None
    observation_date: date
    observer_name: Optional[str] = None
    disease_present: bool
    disease_severity: Optional[str] = None
    incidence_pct: Optional[float] = Field(None, ge=0, le=100)
    severity_rating: Optional[float] = Field(None, ge=0, le=10)
    symptoms_observed: Optional[str] = None
    notes: Optional[str] = None


class DiseaseObservation(BaseModel):
    """Disease observation response"""
    id: int
    farm_id: int
    disease_id: Optional[int] = None
    observed_at: datetime
    observation_date: date
    observer_name: Optional[str] = None
    disease_present: bool
    disease_severity: Optional[str] = None
    incidence_pct: Optional[float] = None
    severity_rating: Optional[float] = None
    symptoms_observed: Optional[str] = None
    confirmed_by_expert: bool
    
    class Config:
        from_attributes = True


class WeatherForecastCreate(BaseModel):
    """Create weather forecast"""
    location: str
    forecast_date: date
    valid_date: date
    forecast_horizon_hours: int
    temperature_min: Optional[float] = None
    temperature_max: Optional[float] = None
    temperature_mean: Optional[float] = None
    humidity_min: Optional[float] = None
    humidity_max: Optional[float] = None
    humidity_mean: Optional[float] = None
    rainfall_total: Optional[float] = None
    rainfall_probability: Optional[float] = None
    wind_speed: Optional[float] = None
    leaf_wetness_hours: Optional[float] = None
    source: str
    confidence: Optional[float] = None


class WeatherForecast(WeatherForecastCreate):
    """Weather forecast response"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
