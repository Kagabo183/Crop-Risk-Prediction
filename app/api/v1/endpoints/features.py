from fastapi import APIRouter, Depends, Query
from datetime import date
from typing import Optional
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.ml.feature_engineering.compute import compute_features

router = APIRouter()

@router.get("/features/")
def get_features(
    region: str = Query("Rwanda"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    
):
    from datetime import date, timedelta
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    features = compute_features(region, start_date, end_date)
    return features
