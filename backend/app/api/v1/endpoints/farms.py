


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.farm import Farm as FarmModel
from app.schemas.farm import Farm, FarmCreate, FarmUpdate

router = APIRouter()

@router.get("/", response_model=List[Farm])
def get_farms(db: Session = Depends(get_db)):
    return db.query(FarmModel).all()

@router.post("/", response_model=Farm)
def create_farm(farm: FarmCreate, db: Session = Depends(get_db)):
    db_farm = FarmModel(**farm.dict())
    db.add(db_farm)
    db.commit()
    db.refresh(db_farm)
    return db_farm

@router.get("/{farm_id}", response_model=Farm)
def get_farm(farm_id: int, db: Session = Depends(get_db)):
    farm = db.query(FarmModel).filter(FarmModel.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

@router.put("/{farm_id}", response_model=Farm)
def update_farm(farm_id: int, farm: FarmCreate, db: Session = Depends(get_db)):
    db_farm = db.query(FarmModel).filter(FarmModel.id == farm_id).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db_farm.name = farm.name
    db_farm.location = farm.location
    db_farm.province = farm.province
    db_farm.crop_type = farm.crop_type
    db_farm.area = farm.area
    db_farm.owner_id = farm.owner_id
    db_farm.latitude = farm.latitude
    db_farm.longitude = farm.longitude
    db.commit()
    db.refresh(db_farm)
    return db_farm


@router.patch("/{farm_id}", response_model=Farm)
def patch_farm(farm_id: int, farm: FarmUpdate, db: Session = Depends(get_db)):
    db_farm = db.query(FarmModel).filter(FarmModel.id == farm_id).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    data = farm.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_farm, key, value)

    db.commit()
    db.refresh(db_farm)
    return db_farm

@router.api_route("/{farm_id}", methods=["DELETE"])
def delete_farm(farm_id: int, db: Session = Depends(get_db)):
    db_farm = db.query(FarmModel).filter(FarmModel.id == farm_id).first()
    if not db_farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    db.delete(db_farm)
    db.commit()
    return {"detail": "Farm deleted"}
