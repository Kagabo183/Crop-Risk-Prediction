from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class PredictionBase(BaseModel):
    farm_id: int
    date: date
    risk_score: float
    yield_loss_percent: Optional[float] = None
    disease_risk_level: Optional[str] = None

class PredictionCreate(PredictionBase):
    pass

class Prediction(PredictionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
