from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Literal, Optional
import joblib
import numpy as np
from datetime import date
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.ml.feature_engineering.compute import compute_features

class FeatureInput(BaseModel):
    ndvi_trend: float
    ndvi_anomaly: float
    rainfall_deficit: float
    heat_stress_days: int
    model: Literal['xgboost', 'mlp'] = 'xgboost'

router = APIRouter()

@router.post("/predict/")
def predict_crop_stress(features: FeatureInput):
    if features.model == 'xgboost':
        model_path = 'crop_stress_xgb_model.pkl'
    else:
        model_path = 'crop_stress_mlp_model.pkl'
    try:
        model = joblib.load(model_path)
    except Exception:
        raise HTTPException(status_code=500, detail=f"Model file {model_path} not found or could not be loaded.")
    X = np.array([[features.ndvi_trend, features.ndvi_anomaly, features.rainfall_deficit, features.heat_stress_days]])
    prob = float(model.predict_proba(X)[0][1])
    pred = int(model.predict(X)[0])
    return {
        "prediction": pred,
        "probability": prob,
        "model": features.model
    }

# Automated prediction endpoint
@router.get("/auto-predict/")
def auto_predict(
    region: str = Query("Rwanda"),
    end_date: Optional[date] = None,
    model: Literal['xgboost', 'mlp'] = 'xgboost',
    db: Session = Depends(get_db),
):
    from datetime import timedelta
    if not end_date:
        end_date = date.today()
    start_date = end_date - timedelta(days=30)
    features = compute_features(region, start_date, end_date, db=db)
    if model == 'xgboost':
        model_path = 'crop_stress_xgb_model.pkl'
    else:
        model_path = 'crop_stress_mlp_model.pkl'
    try:
        clf = joblib.load(model_path)
    except Exception:
        raise HTTPException(status_code=500, detail=f"Model file {model_path} not found or could not be loaded.")
    X = np.array([[features['ndvi_trend'], features['ndvi_anomaly'], features['rainfall_deficit'], features['heat_stress_days']]])
    prob = float(clf.predict_proba(X)[0][1])
    pred = int(clf.predict(X)[0])
    return {
        "region": region,
        "start_date": start_date,
        "end_date": end_date,
        "features": features,
        "prediction": pred,
        "probability": prob,
        "model": model
    }
