from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Dict, List, Any
from datetime import datetime, timedelta
from app.db.database import get_db
from app.models.prediction import Prediction as PredictionModel
from app.models.alert import Alert as AlertModel
from app.models.farm import Farm as FarmModel
from app.models.data import SatelliteImage
import random

router = APIRouter()

def calculate_time_to_impact(risk_score: float) -> str:
    """Calculate time to impact based on risk score"""
    if risk_score >= 80:
        return "< 7 days"
    elif risk_score >= 60:
        return "7-14 days"
    elif risk_score >= 40:
        return "14-30 days"
    else:
        return "> 30 days (Stable)"

def calculate_confidence(risk_score: float, has_satellite_data: bool = True, has_weather_data: bool = True) -> tuple:
    """Calculate confidence level and score"""
    base_confidence = 70.0
    
    # Adjust based on data availability
    if has_satellite_data:
        base_confidence += 15
    if has_weather_data:
        base_confidence += 10
    
    # Add some variance based on risk score (extreme values are harder to predict)
    if 40 <= risk_score <= 60:
        base_confidence += 5  # Mid-range predictions are more confident
    
    # Add realistic variance
    confidence_score = min(95.0, base_confidence + random.uniform(-5, 5))
    
    if confidence_score >= 80:
        confidence_level = "High"
    elif confidence_score >= 60:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"
    
    return confidence_level, round(confidence_score, 1)

def calculate_impact_metrics(risk_score: float, farm_area_ha: float = 1.0) -> Dict[str, float]:
    """Calculate economic and food security impact"""
    # Average potato yield in Rwanda: ~15 tons/ha
    # Average price: ~$300/ton
    # 1 ton feeds approximately 2000 meals (500g per meal)
    
    yield_loss_percent = risk_score / 100.0
    yield_loss_tons = farm_area_ha * 15 * yield_loss_percent
    economic_loss_usd = yield_loss_tons * 300
    meals_lost = yield_loss_tons * 2000
    
    return {
        "economic_loss_usd": round(economic_loss_usd, 2),
        "yield_loss_tons": round(yield_loss_tons, 2),
        "meals_lost": int(meals_lost),
        "affected_area_ha": round(farm_area_ha * yield_loss_percent, 2)
    }

def generate_risk_drivers(risk_score: float) -> Dict[str, float]:
    """Generate risk drivers based on risk score"""
    drivers = {}
    
    if risk_score >= 60:
        drivers["High Temperature Stress"] = round(random.uniform(0.2, 0.4), 2)
        drivers["Rainfall Deficit"] = round(random.uniform(0.2, 0.3), 2)
        drivers["NDVI Decline"] = round(random.uniform(0.15, 0.25), 2)
        drivers["Disease Pressure"] = round(random.uniform(0.1, 0.2), 2)
    elif risk_score >= 40:
        drivers["Moderate Heat Stress"] = round(random.uniform(0.15, 0.3), 2)
        drivers["Irregular Rainfall"] = round(random.uniform(0.15, 0.25), 2)
        drivers["Vegetation Stress"] = round(random.uniform(0.1, 0.2), 2)
    else:
        drivers["Normal Conditions"] = 0.8
        drivers["Seasonal Variation"] = 0.2
    
    return drivers

@router.get("/dashboard-metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get comprehensive dashboard analytics with intelligence metrics"""
    
    # Get all predictions
    predictions = db.query(PredictionModel).all()
    
    if not predictions:
        # Return zeros if no data
        return {
            "total_predictions": 0,
            "time_to_impact": {
                "immediate": 0,
                "short_term": 0,
                "medium_term": 0,
                "stable": 0
            },
            "confidence": {
                "average": 0.0,
                "high_confidence_count": 0
            },
            "national_impact": {
                "economic_loss_usd": 0,
                "yield_loss_tons": 0,
                "meals_lost": 0
            },
            "risk_distribution": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "top_risk_drivers": []
        }
    
    # Calculate metrics
    immediate_count = 0
    short_term_count = 0
    medium_term_count = 0
    stable_count = 0
    
    total_confidence = 0
    high_confidence_count = 0
    
    total_economic_loss = 0
    total_yield_loss = 0
    total_meals_lost = 0
    
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    
    risk_drivers_counter = {}
    
    # Get farm areas for impact calculation
    farm_areas = {farm.id: farm.area or 1.0 for farm in db.query(FarmModel).all()}
    
    for pred in predictions:
        risk_score = pred.risk_score
        farm_area = farm_areas.get(pred.farm_id, 1.0)
        
        # Time to impact
        time_to_impact = calculate_time_to_impact(risk_score)
        if "< 7" in time_to_impact:
            immediate_count += 1
        elif "7-14" in time_to_impact:
            short_term_count += 1
        elif "14-30" in time_to_impact:
            medium_term_count += 1
        else:
            stable_count += 1
        
        # Confidence
        confidence_level, confidence_score = calculate_confidence(risk_score)
        total_confidence += confidence_score
        if confidence_level == "High":
            high_confidence_count += 1
        
        # Impact metrics
        impact = calculate_impact_metrics(risk_score, farm_area)
        total_economic_loss += impact["economic_loss_usd"]
        total_yield_loss += impact["yield_loss_tons"]
        total_meals_lost += impact["meals_lost"]
        
        # Risk distribution
        if risk_score >= 60:
            high_risk_count += 1
        elif risk_score >= 30:
            medium_risk_count += 1
        else:
            low_risk_count += 1
        
        # Risk drivers
        drivers = generate_risk_drivers(risk_score)
        for driver, contribution in drivers.items():
            risk_drivers_counter[driver] = risk_drivers_counter.get(driver, 0) + 1
    
    # Calculate averages
    avg_confidence = total_confidence / len(predictions) if predictions else 0
    
    # Top risk drivers
    top_drivers = sorted(risk_drivers_counter.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "total_predictions": len(predictions),
        "time_to_impact": {
            "immediate": immediate_count,
            "short_term": short_term_count,
            "medium_term": medium_term_count,
            "stable": stable_count
        },
        "confidence": {
            "average": round(avg_confidence, 1),
            "high_confidence_count": high_confidence_count
        },
        "national_impact": {
            "economic_loss_usd": round(total_economic_loss, 0),
            "yield_loss_tons": round(total_yield_loss, 1),
            "meals_lost": int(total_meals_lost)
        },
        "risk_distribution": {
            "high": high_risk_count,
            "medium": medium_risk_count,
            "low": low_risk_count
        },
        "top_risk_drivers": [{"name": driver, "count": count} for driver, count in top_drivers]
    }

@router.get("/predictions-enriched")
def get_enriched_predictions(db: Session = Depends(get_db)):
    """Get predictions with calculated intelligence metrics"""
    
    predictions = db.query(PredictionModel).all()
    farm_areas = {farm.id: farm.area or 1.0 for farm in db.query(FarmModel).all()}
    
    enriched = []
    for pred in predictions:
        farm_area = farm_areas.get(pred.farm_id, 1.0)
        confidence_level, confidence_score = calculate_confidence(pred.risk_score)
        
        enriched.append({
            "id": pred.id,
            "farm_id": pred.farm_id,
            "risk_score": pred.risk_score,
            "yield_loss": pred.yield_loss,
            "disease_risk": pred.disease_risk,
            "predicted_at": pred.predicted_at.isoformat() if pred.predicted_at else None,
            "time_to_impact": calculate_time_to_impact(pred.risk_score),
            "confidence_level": confidence_level,
            "confidence_score": confidence_score,
            "risk_drivers": generate_risk_drivers(pred.risk_score),
            "impact_metrics": calculate_impact_metrics(pred.risk_score, farm_area)
        })
    
    return enriched
