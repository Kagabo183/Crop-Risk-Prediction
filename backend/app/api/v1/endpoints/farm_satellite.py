"""
API endpoint to get the latest satellite data (NDVI) for each farm
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime

from app.db.database import get_db
from app.models.farm import Farm
from app.models.data import SatelliteImage

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_farms_with_satellite_data(db: Session = Depends(get_db)):
    """
    Get all farms with their latest satellite NDVI data.
    Returns farm details plus latest NDVI value, date, and image type.
    """
    farms = db.query(Farm).all()
    result = []
    
    for farm in farms:
        # Get latest satellite image for this farm (from extra_metadata farm_id)
        # Using Python filtering instead of JSON query for broader compatibility
        all_images = (
            db.query(SatelliteImage)
            .order_by(desc(SatelliteImage.date))
            .all()
        )
        
        latest_image = None
        for img in all_images:
            if img.extra_metadata and img.extra_metadata.get('farm_id') == farm.id:
                latest_image = img
                break
        
        farm_data = {
            "id": farm.id,
            "name": farm.name,
            "location": farm.location,
            "area": farm.area,
            "latitude": getattr(farm, 'latitude', None),
            "longitude": getattr(farm, 'longitude', None),
            "ndvi": None,
            "ndvi_date": None,
            "image_type": None,
            "ndvi_status": "unknown",
            "data_source": "simulated"  # Default to simulated
        }
        
        if latest_image and latest_image.extra_metadata:
            ndvi_value = latest_image.extra_metadata.get('ndvi_value')
            if ndvi_value is not None:
                farm_data["ndvi"] = round(ndvi_value, 4)
                farm_data["ndvi_date"] = latest_image.date.isoformat() if latest_image.date else None
                farm_data["image_type"] = latest_image.image_type
                
                # Check if real sentinel-2 data
                source = latest_image.extra_metadata.get('source', 'simulated')
                farm_data["data_source"] = "real" if source == "sentinel2_real" else "simulated"
                farm_data["tile"] = latest_image.extra_metadata.get('tile')
                farm_data["cloud_cover"] = latest_image.extra_metadata.get('cloud_cover')
                
                # Classify NDVI status
                if ndvi_value >= 0.6:
                    farm_data["ndvi_status"] = "healthy"
                elif ndvi_value >= 0.3:
                    farm_data["ndvi_status"] = "moderate"
                else:
                    farm_data["ndvi_status"] = "stressed"
        
        result.append(farm_data)
    
    return result


@router.get("/history/{farm_id}")
def get_farm_ndvi_history(farm_id: int, limit: int = 30, db: Session = Depends(get_db)):
    """
    Get NDVI time series for a specific farm.
    Returns up to `limit` most recent satellite observations.
    """
    # Get all images and filter by farm_id in Python
    all_images = (
        db.query(SatelliteImage)
        .order_by(desc(SatelliteImage.date))
        .all()
    )
    
    images = [img for img in all_images if img.extra_metadata and img.extra_metadata.get('farm_id') == farm_id][:limit]
    
    history = []
    for img in images:
        if img.extra_metadata and 'ndvi_value' in img.extra_metadata:
            history.append({
                "date": img.date.isoformat() if img.date else None,
                "ndvi": round(img.extra_metadata['ndvi_value'], 4),
                "image_type": img.image_type,
                "cloud_coverage": img.extra_metadata.get('cloud_coverage', 0)
            })
    
    # Sort chronologically
    history.reverse()
    return history
