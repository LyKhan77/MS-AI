from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.counting_logic import counting_service
import os

router = APIRouter()

class SessionStartRequest(BaseModel):
    name: str
    target: int

class SessionStatus(BaseModel):
    name: str
    current_count: int
    target_count: int
    is_active: bool

# Simple in-memory session store for now
current_session = {
    "name": "Default",
    "target": 100,
    "active": False
}

@router.post("/start")
def start_session(data: SessionStartRequest):
    current_session["name"] = data.name
    current_session["target"] = data.target
    current_session["active"] = True
    
    # Reset Logic
    counting_service.reset_count()
    
    return {"status": "started", "session": current_session}

@router.post("/stop")
def stop_session():
    current_session["active"] = False
    return {"status": "stopped", "final_count": counting_service.count}

@router.get("/status")
def get_session_status():
@router.get("/list")
def list_sessions():
    # Verify path exists
    base_path = "data/media/sessions"
    if not os.path.exists(base_path):
        return []
    
    sessions = []
    for d in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, d)):
            sessions.append(d)
    return sessions

@router.get("/{session_id}/images")
def list_session_images(session_id: str):
    path = os.path.join("data/media/sessions", session_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found")
    
    images = []
    for f in os.listdir(path):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            # Return relative path for frontend to construct URL or full path for API
            images.append({
                "name": f,
                "path": os.path.join(path, f)
            })
    return images
