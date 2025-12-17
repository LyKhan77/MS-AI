from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from app.services.camera_manager import camera_manager
from pydantic import BaseModel
import shutil
import os
import cv2
import time

router = APIRouter()

class StreamConfig(BaseModel):
    mode: str  # "rtsp" or "file"
    path: str

@router.post("/config")
def configure_stream(config: StreamConfig):
    """
    Configure the video source (RTSP or File)
    """
    try:
        camera_manager.set_source(config.mode, config.path)
        camera_manager.start()
        return {"status": "success", "message": f"Source set to {config.mode}: {config.path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file to be used as input source
    """
    upload_dir = "data/media/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"filename": file.filename, "path": file_path}

from app.services.counting_logic import counting_service

def generate_frames():
    while True:
        frame = camera_manager.get_frame()
        if frame is None:
            time.sleep(0.01)
            continue
        
        # Process frame with Counting Logic (YOLO + State Machine)
        # This returns the annotated frame (with boxes)
        annotated_frame, _ = counting_service.process_frame(frame)
        
        # Encode as JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@router.get("/video_feed")
def video_feed():
    """
    MJPEG Stream for the Frontend
    """
    # Auto start if not running
    if not camera_manager.running:
        camera_manager.start()
        
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@router.get("/status")
def get_status():
    return {
        "running": camera_manager.running,
        "source_type": camera_manager.source_type,
        "source_path": camera_manager.source_path
    }
