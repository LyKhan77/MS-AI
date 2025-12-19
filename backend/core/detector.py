from ultralytics import YOLOWorld
import cv2
import os
from config import Config

class MetalSheetCounter:
    def __init__(self):
        self.model_path = Config.YOLO_MODEL_PATH
        # Load local model or download if not exists (Ultralytics handles downloads usually)
        self.model = YOLOWorld(self.model_path)
        
        # Define what we are looking for
        self.model.set_classes(["metal sheet", "rectangular plate", "steel plate", "iron sheet", "aluminum sheet", "silver sheet"])
        
        self.current_count = 0
        self.last_detection_time = 0
        self.cooldown = 1.0 # Seconds between counts to prevent double counting same sheet jitter
        
        # Session handling
        self.session_id = None
        self.captures_dir = None

    def set_session(self, session_id, captures_dir):
        self.session_id = session_id
        self.captures_dir = captures_dir
        self.current_count = 0 

    def process(self, frame):
        """
        Run detection on the frame.
        If a NEW sheet is stable-detected, increment count and save capture.
        """
        results = self.model.predict(frame, conf=0.25, verbose=False)
        annotated_frame = results[0].plot()
        
        # Counting Logic (Simplified for Demo)
        # In a real top-down scenario, typically we look for "Object enters ROI" or "Object covers center".
        # Here we will assume if we see a 'metal sheet' with high confidence 
        # AND we haven't counted one recently (cooldown), we count it.
        # Ideally, we should track IDs. YOLO tracks IDs if we use model.track().
        
        detections = results[0].boxes
        if len(detections) > 0:
            # Check if it's a new object? 
            # For simplicity, let's use a center-point check or just basic presence + cooldown.
            # Real implementation would use SORT/DeepSORT tracking.
            
            # Simple Logic: If detection is valid and cooldown passed
            import time
            now = time.time()
            if now - self.last_detection_time > self.cooldown:
                self.increment_count(frame)
                self.last_detection_time = now
        
        return self.current_count, annotated_frame

    def increment_count(self, frame):
        self.current_count += 1
        if self.session_id and self.captures_dir:
            filename = f"sheet_{self.current_count}_{int(time.time())}.jpg"
            save_path = os.path.join(self.captures_dir, filename)
            cv2.imwrite(save_path, frame)
            # TODO: Update DB with new count (done via main app callback usually)
            
    def get_count(self):
        return self.current_count
