from fastapi import APIRouter
from pydantic import BaseModel
from app.services.dimension_calc import dimension_service

router = APIRouter()

class CalibrationSettings(BaseModel):
    pixel_to_mm_ratio: float

@router.get("/")
def get_settings():
    return {
        "calibration": {
            "pixel_to_mm_ratio": dimension_service.pixel_to_mm_ratio
        }
    }

@router.post("/calibration")
def update_calibration(settings: CalibrationSettings):
    dimension_service.pixel_to_mm_ratio = settings.pixel_to_mm_ratio
    return {"status": "updated", "pixel_to_mm_ratio": dimension_service.pixel_to_mm_ratio}
