from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class PredictionBase(BaseModel):
    farm_id: int
    risk_score: float
    yield_loss: Optional[float] = None
    disease_risk: Optional[str] = None

class PredictionCreate(PredictionBase):
    pass

class Prediction(PredictionBase):
    id: int
    predicted_at: datetime
    
    # Advanced intelligence fields
    time_to_impact: Optional[str] = None
    confidence_level: Optional[str] = None
    confidence_score: Optional[float] = None
    risk_drivers: Optional[Dict[str, float]] = None
    risk_explanation: Optional[str] = None
    recommendations: Optional[List[Dict[str, str]]] = None
    impact_metrics: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
