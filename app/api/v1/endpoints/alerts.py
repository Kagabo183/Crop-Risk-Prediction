
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.alert import Alert as AlertModel
from app.schemas.alert import Alert, AlertCreate

router = APIRouter()

@router.get("/", response_model=List[Alert])
def get_alerts(db: Session = Depends(get_db)):
    return db.query(AlertModel).all()

@router.post("/", response_model=Alert)
def create_alert(alert: AlertCreate, db: Session = Depends(get_db)):
    db_alert = AlertModel(**alert.dict())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.get("/{alert_id}", response_model=Alert)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.put("/{alert_id}", response_model=Alert)
def update_alert(alert_id: int, alert: AlertCreate, db: Session = Depends(get_db)):
    db_alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    for field, value in alert.dict().items():
        setattr(db_alert, field, value)
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.api_route("/{alert_id}", methods=["DELETE"])
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    db_alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if not db_alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(db_alert)
    db.commit()
    return {"detail": "Alert deleted"}
