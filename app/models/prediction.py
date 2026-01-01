from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    predicted_at = Column(DateTime, default=datetime.utcnow)
    risk_score = Column(Float, nullable=False)
    yield_loss = Column(Float, nullable=True)
    disease_risk = Column(String, nullable=True)
    
    # Advanced intelligence fields
    time_to_impact = Column(String, nullable=True)  # "< 7 days", "7-14 days", etc.
    confidence_level = Column(String, nullable=True)  # "High", "Medium", "Low"
    confidence_score = Column(Float, nullable=True)  # 0-100
    risk_drivers = Column(JSON, nullable=True)  # {"ndvi_trend": 41, "rainfall": 33, ...}
    risk_explanation = Column(Text, nullable=True)  # Human-readable explanation
    recommendations = Column(JSON, nullable=True)  # List of actionable recommendations
    impact_metrics = Column(JSON, nullable=True)  # Economic/policy metrics
    
    farm = relationship("Farm")
