from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
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
    farm = relationship("Farm")
