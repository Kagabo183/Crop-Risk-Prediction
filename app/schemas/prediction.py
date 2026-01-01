from pydantic import BaseModel
from typing import Optional
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

    class Config:
        from_attributes = True
