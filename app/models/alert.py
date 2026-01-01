from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=False)
    message = Column(String, nullable=False)
    level = Column(String(20), nullable=False)  # e.g., 'low', 'medium', 'high'
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    farm = relationship("Farm")
