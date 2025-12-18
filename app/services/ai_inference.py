"""
AI Inference Module
Wrapper for YOLO model inference with GPU optimization
"""

import torch
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ultralytics import YOLO


class AIInference:
    """AI model inference wrapper for metal sheet detection"""
    
    def __init__(self, model_path: str, device: str = 'cuda', conf_threshold: float = 0.8):
        """
        Initialize AI inference
        
        Args:
            model_path: Path to YOLO model file (.pt)
            device: 'cuda' or 'cpu'
            conf_threshold: Confidence threshold
        """
        self.model_path = Path(model_path)
        self.device = device if torch.cuda.is_available() else 'cpu'
        self.conf_threshold = conf_threshold
        
        # Model
        self.model: Optional[YOLO] = None
        self.is_loaded = False
        
        # Stats
        self.inference_count = 0
        self.avg_inference_time = 0.0
        
        print(f"AI Inference initialized")
        print(f"  Device: {self.device}")
        print(f"  Confidence threshold: {self.conf_threshold}")
    
    def load_model(self) -> bool:
        """
        Load YOLO model
        
        Returns:
            True if loaded successfully
        """
        if not self.model_path.exists():
            print(f"Model file not found: {self.model_path}")
            return False
        
        try:
            print(f"Loading model from: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            
            # Move to device
            if self.device == 'cuda' and torch.cuda.is_available():
                self.model.to('cuda')
                print("Model moved to CUDA")
            
            # Warmup
            print("Warming up model...")
            dummy_input = np.zeros((640, 640, 3), dtype=np.uint8)
            _ = self.model(dummy_input, verbose=False)
            
            self.is_loaded = True
            print("Model loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print("Model unloaded")
    
    def detect(self, frame: np.ndarray, conf: float = None) -> List[Dict]:
        """
        Run detection on frame
        
        Args:
            frame: Input frame (BGR)
            conf: Optional confidence override
            
        Returns:
            List of detections [{'bbox': [x1,y1,x2,y2], 'confidence': float, 'class_name': str}]
        """
        if not self.is_loaded:
            print("Model not loaded")
            return []
        
        try:
            # Use provided conf or default
            confidence = conf if conf is not None else self.conf_threshold
            
            # Run inference
            import time
            start_time = time.time()
            
            results = self.model(
                frame,
                conf=confidence,
                verbose=False,
                device=self.device
            )
            
            inference_time = (time.time() - start_time) * 1000  # ms
            
            # Update stats
            self.inference_count += 1
            self.avg_inference_time = (
                (self.avg_inference_time * (self.inference_count - 1) + inference_time) 
                / self.inference_count
            )
            
            # Parse results
            detections = []
            
            if len(results) > 0:
                result = results[0]
                boxes = result.boxes
                
                for box in boxes:
                    # Get bbox coordinates
                    xyxy = box.xyxy[0].cpu().numpy()
                    conf_score = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # Get class name
                    class_name = result.names[cls_id] if result.names else f"class_{cls_id}"
                    
                    detections.append({
                        'bbox': xyxy.tolist(),  # [x1, y1, x2, y2]
                        'confidence': conf_score,
                        'class_id': cls_id,
                        'class_name': class_name
                    })
            
            return detections
            
        except Exception as e:
            print(f"Error during inference: {e}")
            return []
    
    def detect_and_draw(self, frame: np.ndarray, conf: float = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        Run detection and draw bounding boxes on frame
        
        Args:
            frame: Input frame (BGR)
            conf: Optional confidence override
            
        Returns:
            (annotated_frame, detections)
        """
        detections = self.detect(frame, conf)
        annotated_frame = frame.copy()
        
        # Draw bounding boxes
        for det in detections:
            x1, y1, x2, y2 = [int(c) for c in det['bbox']]
            confidence = det['confidence']
            class_name = det['class_name']
            
            # Draw box (primary color #003473)
            color = (115, 52, 0)  # BGR format of #003473
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
            
            # Draw glow effect
            cv2.rectangle(annotated_frame, (x1-1, y1-1), (x2+1, y2+1), (180, 100, 0), 1)
            cv2.rectangle(annotated_frame, (x1-2, y1-2), (x2+2, y2+2), (210, 150, 50), 1)
            
            # Draw label
            label = f"{class_name} {confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Label background
            cv2.rectangle(
                annotated_frame,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0] + 10, y1),
                color,
                -1
            )
            
            # Label text
            cv2.putText(
                annotated_frame,
                label,
                (x1 + 5, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
        
        return annotated_frame, detections
    
    def get_stats(self) -> Dict:
        """
        Get inference statistics
        
        Returns:
            Stats dict
        """
        return {
            'is_loaded': self.is_loaded,
            'device': self.device,
            'cuda_available': torch.cuda.is_available(),
            'inference_count': self.inference_count,
            'avg_inference_time_ms': round(self.avg_inference_time, 2),
            'confidence_threshold': self.conf_threshold
        }
