
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.prediction import Prediction as PredictionModel
from app.schemas.prediction import Prediction, PredictionCreate

router = APIRouter()

@router.get("/", response_model=List[Prediction])
def get_predictions(db: Session = Depends(get_db)):
    return db.query(PredictionModel).all()

@router.post("/", response_model=Prediction)
def create_prediction(prediction: PredictionCreate, db: Session = Depends(get_db)):
    db_prediction = PredictionModel(**prediction.dict())
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

@router.get("/{prediction_id}", response_model=Prediction)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = db.query(PredictionModel).filter(PredictionModel.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction

@router.put("/{prediction_id}", response_model=Prediction)
def update_prediction(prediction_id: int, prediction: PredictionCreate, db: Session = Depends(get_db)):
    db_prediction = db.query(PredictionModel).filter(PredictionModel.id == prediction_id).first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    for field, value in prediction.dict().items():
        setattr(db_prediction, field, value)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction

@router.api_route("/{prediction_id}", methods=["DELETE"])
def delete_prediction(prediction_id: int, db: Session = Depends(get_db)):
    db_prediction = db.query(PredictionModel).filter(PredictionModel.id == prediction_id).first()
    if not db_prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    db.delete(db_prediction)
    db.commit()
    return {"detail": "Prediction deleted"}
