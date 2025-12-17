from ultralytics import YOLO
import logging
import torch

logger = logging.getLogger(__name__)

class YOLOWrapper:
    def __init__(self, model_path: str = "yolov8n.pt"):
        self.model_path = model_path
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def load_model(self):
        if self.model is None:
            logger.info(f"Loading YOLO model from {self.model_path} to {self.device}")
            self.model = YOLO(self.model_path)
            # Warmup
            # self.model.predict("https://ultralytics.com/images/bus.jpg", verbose=False) 
            
    def unload_model(self):
        if self.model:
            del self.model
            torch.cuda.empty_cache()
            self.model = None
            logger.info("YOLO model unloaded")

    def predict(self, frame, conf=0.5):
        if self.model is None:
            self.load_model()
        
        # Stream=True for memory efficiency in loops
        results = self.model.predict(frame, conf=conf, device=self.device, verbose=False)
        return results[0]

# Singleton-ish usage usually, but we might want multiple
# One for counting (nano), one for defect (heavy)
counting_model = YOLOWrapper("yolov8n.pt") # Placeholder for counting model
defect_model = YOLOWrapper("yolov8n.pt")   # Placeholder for defect model (NEU-DET)
