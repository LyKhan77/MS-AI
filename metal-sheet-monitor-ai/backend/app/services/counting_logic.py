import time
import logging
from enum import Enum
from app.services.ai.wrapper_yolo import counting_model

logger = logging.getLogger(__name__)

class CountingState(Enum):
    STABLE_EMPTY = 0
    MOTION_OCCLUSION = 1
    NEW_OBJECT_STABILIZING = 2

class VotingBuffer:
    """Helper to smooth out detections over N frames"""
    def __init__(self, size=5):
        self.size = size
        self.buffer = []
    
    def add(self, is_detected):
        self.buffer.append(is_detected)
        if len(self.buffer) > self.size:
            self.buffer.pop(0)
    
    def is_consistent_true(self):
        return len(self.buffer) == self.size and all(self.buffer)

class CountingLogic:
    def __init__(self):
        self.count = 0
        self.state = CountingState.STABLE_EMPTY
        self.last_stable_time = time.time()
        self.cooldown = 0
        
        # Thresholds
        self.motion_threshold = 0.5 # Placeholder for pixel diff
        self.confidence_threshold = 0.6
        
        # Buffer for logical debouncing
        self.detection_buffer = VotingBuffer(size=3)

    def process_frame(self, frame, run_ml=True):
        """
        Main loop to process frame.
        Returns (annotated_frame, current_count)
        """
        # 1. Simple Motion Check (Optimization: Don't run YOLO if no motion?)
        # For now, let's run YOLO every frame if hardware allows (Orin Nano supports ~30fps YOLOv8n)
        
        detections = []
        annotated_frame = frame
        
        if run_ml:
            result = counting_model.predict(frame, conf=self.confidence_threshold)
            annotated_frame = result.plot()
            
            # Check if "metal_sheet" class is present
            # Assuming 'person' or class 0 is metal count for now as placeholder
            has_metal = False
            for box in result.boxes:
                # cls_id = int(box.cls[0]) 
                # if cls_id == TARGET_CLASS_ID:
                has_metal = True # Assume any detection is valid for now
                break
                
            self.detection_buffer.add(has_metal)
            
            # State Machine
            is_stable_metal = self.detection_buffer.is_consistent_true()
             
            if self.state == CountingState.STABLE_EMPTY:
                if is_stable_metal:
                   if time.time() - self.cooldown > 2.0: # 2 sec debounce
                       self.state = CountingState.NEW_OBJECT_STABILIZING
                       # TRIGGER COUNT
                       self.count += 1
                       self.cooldown = time.time()
                       logger.info(f"Count Incremented! Total: {self.count}")
                       # Trigger Auto-Capture here
            
            elif self.state == CountingState.NEW_OBJECT_STABILIZING:
                if not has_metal: # Object removed or occlusion
                     self.state = CountingState.STABLE_EMPTY

        return annotated_frame, self.count

    def reset_count(self):
        self.count = 0

counting_service = CountingLogic()
