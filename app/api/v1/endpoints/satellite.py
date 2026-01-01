from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List
from app.db.database import get_db
from app.models.data import SatelliteImage as SatelliteImageModel
from app.schemas.data import SatelliteImage

router = APIRouter()

@router.get("/", response_model=List[SatelliteImage])
def get_satellite_images(db: Session = Depends(get_db)):
    return db.query(SatelliteImageModel).order_by(SatelliteImageModel.date.desc()).limit(100).all()

@router.get("/count", response_model=int)
def get_satellite_image_count(db: Session = Depends(get_db)):
    from app.models.data import SatelliteImage as SatelliteImageModel
    return db.query(SatelliteImageModel).count()
