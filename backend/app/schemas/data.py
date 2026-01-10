from pydantic import BaseModel
from typing import Optional, Any
from datetime import date

class SatelliteImage(BaseModel):
    id: int
    date: date
    region: str
    image_type: str
    file_path: str
    extra_metadata: Optional[Any]

    class Config:
        from_attributes = True
