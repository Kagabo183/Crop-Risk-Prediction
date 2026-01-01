from pydantic import BaseModel
from typing import Optional

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    area: Optional[float] = None
    owner_id: Optional[int] = None

class FarmCreate(FarmBase):
    pass

class Farm(FarmBase):
    id: int

    class Config:
        from_attributes = True
