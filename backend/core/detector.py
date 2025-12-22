from ultralytics import YOLO
import cv2
import os
import time
import numpy as np
from config import Config
from core.tracker import Sort


class MetalSheetCounter:
    def __init__(self):
        self.model_path = Config.YOLO_MODEL_PATH
        # Load custom trained model
        self.model = YOLO(self.model_path)
        print(f"[YOLO] Loaded custom model from: {self.model_path}")
        print(f"[YOLO] Model classes: {self.model.names}")
        
        self.current_count = 0
        
        # Replace cooldown with SORT tracker
        self.tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.3)
        self.counted_ids = set()  # Track which IDs have been counted
        
        # Session handling
        self.session_id = None
        self.captures_dir = None
        self.confidence = 0.25  # Default confidence

    def set_session(self, session_id, captures_dir, confidence=0.25):
        self.session_id = session_id
        self.captures_dir = captures_dir
        self.current_count = 0
        self.confidence = confidence
        
        # Reset tracker and counted IDs for new session
        self.tracker = Sort(max_age=30, min_hits=3, iou_threshold=0.3)
        self.counted_ids = set()
        print(f"[DETECTOR] Session set with confidence: {confidence}, tracker reset")

    def process(self, frame):
        """
        Run detection and tracking on the frame.
        Count each unique tracked object exactly once.
        """
        if not hasattr(self, '_process_logged'):
            print(f"[DETECTOR] Processing with SORT tracking, session: {self.session_id}, confidence: {self.confidence}")
            self._process_logged = True
        
        # Run YOLO detection
        results = self.model.predict(frame, conf=self.confidence, verbose=False)
        
        # Extract detections as [x1, y1, x2, y2, conf]
        detections = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = box.conf[0].item()
            detections.append([x1, y1, x2, y2, conf])
        
        # Update tracker
        if len(detections) > 0:
            tracked_objects = self.tracker.update(np.array(detections))
        else:
            tracked_objects = self.tracker.update(np.empty((0, 5)))
        
        # Count new objects
        for obj in tracked_objects:
            track_id = int(obj[4])
            if track_id not in self.counted_ids:
                self.counted_ids.add(track_id)
                # Save capture with bbox
                bbox = obj[:4]
                self.increment_count(frame, bbox=bbox)
        
        # Draw tracked boxes
        annotated_frame = self._draw_tracks(frame.copy(), tracked_objects)
        
        return self.current_count, annotated_frame
    
    def _draw_tracks(self, frame, tracked_objects):
        """Draw bounding boxes with track IDs"""
        for obj in tracked_objects:
            x1, y1, x2, y2, track_id = obj
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            track_id = int(track_id)
            
            # Color: Green if counted, Orange if tracking
            color = (0, 255, 0) if track_id in self.counted_ids else (0, 165, 255)
            
            # Draw box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw track ID
            label = f"ID:{track_id}"
            if track_id in self.counted_ids:
                label += " ✓"
            
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame

    def increment_count(self, frame, bbox=None):
        """Increment count and save capture (cropped to bbox if provided)"""
        self.current_count += 1
        
        if self.captures_dir and self.session_id:
            os.makedirs(self.captures_dir, exist_ok=True)
            filename = f"sheet_{self.current_count}_{int(time.time())}.jpg"
            filepath = os.path.join(self.captures_dir, filename)
            
            # Crop to bounding box if provided
            if bbox is not None:
                x1, y1, x2, y2 = bbox
                cropped = frame[int(y1):int(y2), int(x1):int(x2)]
                cv2.imwrite(filepath, cropped)
            else:
                cv2.imwrite(filepath, frame)
            
    def get_count(self):
        return self.current_count
