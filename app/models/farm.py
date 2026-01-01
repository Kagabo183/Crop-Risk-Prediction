from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base

class Farm(Base):
    __tablename__ = "farms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    area = Column(Float, nullable=True)  # in hectares
    owner_id = Column(Integer, nullable=True)  # FK to User, can be set up later
