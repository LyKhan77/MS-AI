from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.services.ai.wrapper_yolo import defect_model
from app.services.ai.wrapper_sam import sam_service
from app.services.ai.wrapper_yolo import counting_model
import cv2
import numpy as np
import os

router = APIRouter()

class AnalyzeRequest(BaseModel):
    image_path: str # Path to the image relative to data/media

@router.post("/analyze")
def analyze_defect(req: AnalyzeRequest):
    """
    Full Defect Analysis Pipeline:
    1. Load Image
    2. Detect Defects (YOLO) -> get Bboxes
    3. Segment Defects (SAM 2) -> get Masks
    4. Save Crops
    """
    full_path = req.image_path
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image not found")
        
    image = cv2.imread(full_path)
    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # 1. Unload Counting Model to free VRAM
    counting_model.unload_model()
    
    # 2. Detect Defects (bounding boxes) using NEU-DET model
    # Note: We use the defect_model wrapper
    results = defect_model.predict(image, conf=0.25)
    
    defects_found = []
    
    for i, box in enumerate(results.boxes):
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cls_id = int(box.cls[0])
        # class_name = results.names[cls_id]
        
        # 3. Segment using SAM 2
        # SAM 2 needs to be loaded (auto handled by wrapper)
        mask = sam_service.predict(image, box_prompt=[x1, y1, x2, y2])
        
        # 4. Save Crop and visualization
        # Apply mask to image? or just save crop
        # Let's simple crop for now
        crop = image[int(y1):int(y2), int(x1):int(x2)]
        crop_filename = f"{os.path.basename(full_path).split('.')[0]}_defect_{i}.png"
        crop_path = os.path.join(os.path.dirname(full_path), crop_filename)
        cv2.imwrite(crop_path, crop)
        
        defects_found.append({
            "id": i,
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "crop_path": crop_path
        })
        
    # Free up SAM 2 after analysis batch?
    # sam_service.unload_model() 
    # Maybe keep it if user is doing batch analysis
    
    return {"status": "completed", "defects": defects_found}
