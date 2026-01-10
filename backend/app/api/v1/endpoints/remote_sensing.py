"""Remote sensing diagnostics API.

Provides a best-effort farm diagnostic combining:
- Sentinel-derived NDVI signals (cover, stress, trend)
- Weather-driven disease model ranking

This does NOT claim definitive crop species or disease confirmation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.remote_sensing_diagnostics import RemoteSensingDiagnosticsService


router = APIRouter()


@router.get("/diagnostics/{farm_id}")
def get_remote_sensing_diagnostics(
    farm_id: int,
    days: int = Query(30, ge=1, le=365),
    top_n: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    """Return NDVI-based signals + ranked disease risks for a farm."""
    try:
        svc = RemoteSensingDiagnosticsService()
        return svc.diagnose_farm(farm_id=farm_id, db=db, days=days, top_n=top_n)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostics failed: {e}")
