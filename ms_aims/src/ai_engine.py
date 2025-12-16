# src/ai_engine.py
import cv2
import numpy as np
import time

class AIEngine:
    def __init__(self):
        self.model = None
        self.is_ready = False
        
        # Threshold settings (Simple HSV or Grayscale for now)
        # Assuming dark metal on light table or vice versa
        self.threshold_val = 127 

    def load_model(self):
        """
        For Phase 2, we initialize the 'model' as simply ready for CV operations.
        Future: Load NanoSAM/TensorRT engine here.
        """
        print("Initializing Computer Vision Engine...")
        time.sleep(0.5) 
        self.is_ready = True
        print("CV Engine Ready.")

    def run_segmentation(self, frame):
        """
        Phase 2: Use Thresholding to find the object.
        Returns: largest_contour (or None)
        """
        if not self.is_ready or frame is None:
            return None
            
        # 1. Convert to Grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. Gaussian Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Thresholding (OTSU is good for bimodal distributions)
        # Note: Adjust cv2.THRESH_BINARY_INV depending on if object is dark or light
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 4. Find Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # 5. Get largest contour (assume it's the metal sheet)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Filter small noise
        if cv2.contourArea(largest_contour) < 1000: # Minimum area threshold
            return None
            
        return largest_contour

    def detect_defects(self, mask, frame):
        """
        Analyze area within mask for defects.
        """
        pass
