"""
Image processing utilities for metal sheet detection
Includes ROI handling, dimension calculation, and quality analysis
"""

import cv2
import numpy as np
from typing import Tuple, List, Optional, Dict
import logging
import os
from datetime import datetime
from PIL import Image
import json

logger = logging.getLogger(__name__)


class ROIManager:
    """Region of Interest manager for workspace focusing"""
    
    def __init__(self):
        self.roi_points = []
        self.roi_mask = None
        self.roi_set = False
    
    def set_roi(self, points: List[Tuple[int, int]], image_shape: Tuple[int, int]):
        """
        Set region of interest polygon
        
        Args:
            points: List of (x, y) points defining ROI polygon
            image_shape: (height, width) of the image
        """
        self.roi_points = points
        self.roi_mask = np.zeros(image_shape[:2], dtype=np.uint8)
        cv2.fillPoly(self.roi_mask, [np.array(points)], 255)
        self.roi_set = True
        logger.info(f"ROI set with {len(points)} points")
    
    def apply_roi(self, image: np.ndarray) -> np.ndarray:
        """
        Apply ROI mask to image
        
        Args:
            image: Input image
            
        Returns:
            np.ndarray: ROI masked image
        """
        if not self.roi_set or self.roi_mask is None:
            return image
        
        # Ensure mask matches image size
        if self.roi_mask.shape[:2] != image.shape[:2]:
            self.roi_mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(self.roi_mask, [np.array(self.roi_points)], 255)
        
        return cv2.bitwise_and(image, image, mask=self.roi_mask)
    
    def get_roi_mask(self, image_shape: Tuple[int, int]) -> np.ndarray:
        """
        Get ROI mask for given image shape
        
        Args:
            image_shape: (height, width) of image
            
        Returns:
            np.ndarray: ROI mask
        """
        if not self.roi_set:
            return np.ones(image_shape[:2], dtype=np.uint8) * 255
        
        if self.roi_mask is None or self.roi_mask.shape[:2] != image_shape[:2]:
            self.roi_mask = np.zeros(image_shape[:2], dtype=np.uint8)
            cv2.fillPoly(self.roi_mask, [np.array(self.roi_points)], 255)
        
        return self.roi_mask
    
    def reset_roi(self):
        """Reset ROI to full image"""
        self.roi_points = []
        self.roi_mask = None
        self.roi_set = False


class DimensionCalculator:
    """Calculator for converting pixel measurements to real-world dimensions"""
    
    def __init__(self, pixel_to_mm_ratio: float = 1.0):
        """
        Initialize dimension calculator
        
        Args:
            pixel_to_mm_ratio: Conversion ratio from pixels to millimeters
        """
        self.pixel_to_mm_ratio = pixel_to_mm_ratio
        self.calibration_points = []
        self.calibrated = False
    
    def set_calibration(self, pixel_length: float, real_length: float):
        """
        Set calibration ratio
        
        Args:
            pixel_length: Length in pixels
            real_length: Length in millimeters
        """
        self.pixel_to_mm_ratio = real_length / pixel_length
        self.calibrated = True
        logger.info(f"Calibration set: {pixel_length}px = {real_length}mm ({self.pixel_to_mm_ratio:.4f} px/mm)")
    
    def pixels_to_mm(self, pixels: float) -> float:
        """
        Convert pixels to millimeters
        
        Args:
            pixels: Length in pixels
            
        Returns:
            float: Length in millimeters
        """
        return pixels * self.pixel_to_mm_ratio
    
    def mm_to_pixels(self, mm: float) -> float:
        """
        Convert millimeters to pixels
        
        Args:
            mm: Length in millimeters
            
        Returns:
            float: Length in pixels
        """
        return mm / self.pixel_to_mm_ratio
    
    def calculate_sheet_dimensions(self, mask: np.ndarray) -> Dict[str, float]:
        """
        Calculate dimensions of a metal sheet from mask
        
        Args:
            mask: Binary mask of the sheet
            
        Returns:
            dict: Dimensions including length, width, area, and angle
        """
        # Find contours
        contours, _ = cv2.findContours(
            mask.astype(np.uint8) * 255,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            return {"length": 0, "width": 0, "area": 0, "angle": 0, "center_x": 0, "center_y": 0}
        
        # Get largest contour
        contour = max(contours, key=cv2.contourArea)
        
        # Minimum area rectangle (rotated bounding box)
        rect = cv2.minAreaRect(contour)
        (center, (width, height), angle) = rect
        
        # Convert to real-world dimensions
        length_px = max(width, height)
        width_px = min(width, height)
        area_px = cv2.contourArea(contour)
        
        result = {
            "length": self.pixels_to_mm(length_px),
            "width": self.pixels_to_mm(width_px),
            "area": self.pixels_to_mm(np.sqrt(area_px)) ** 2,  # Convert area
            "angle": angle,
            "center_x": center[0],
            "center_y": center[1]
        }
        
        return result


class QualityAnalyzer:
    """Analyzer for surface quality and defect detection"""
    
    def __init__(self, sensitivity: float = 0.1):
        """
        Initialize quality analyzer
        
        Args:
            sensitivity: Sensitivity threshold for defect detection (0.0-1.0)
        """
        self.sensitivity = sensitivity
    
    def analyze_surface_quality(self, image: np.ndarray, mask: np.ndarray) -> Dict:
        """
        Analyze surface quality within masked region
        
        Args:
            image: Original image
            mask: Binary mask of region to analyze
            
        Returns:
            dict: Quality analysis results
        """
        # Apply mask to image
        masked_image = cv2.bitwise_and(image, image, mask=mask.astype(np.uint8))
        
        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(masked_image, cv2.COLOR_BGR2HSV)
        
        # Extract masked region
        masked_region = gray[mask > 0]
        hsv_region = hsv[mask > 0]
        
        if len(masked_region) == 0:
            return {"status": "NG", "defects": [], "confidence": 0.0, "reason": "No valid region"}
        
        # Texture analysis
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / np.sum(mask > 0)
        
        # Histogram analysis for color consistency
        hist_h = cv2.calcHist([hsv], [0], mask.astype(np.uint8), [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], mask.astype(np.uint8), [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], mask.astype(np.uint8), [256], [0, 256])
        
        # Calculate histogram uniformity
        h_uniformity = np.std(hist_h) / (np.mean(hist_h) + 1e-6)
        s_uniformity = np.std(hist_s) / (np.mean(hist_s) + 1e-6)
        v_uniformity = np.std(hist_v) / (np.mean(hist_v) + 1e-6)
        
        # Statistical analysis
        mean_intensity = np.mean(masked_region)
        std_intensity = np.std(masked_region)
        
        # Detect potential defects
        defects = []
        
        # Scratches detection (high variance in edges)
        if edge_density > self.sensitivity * 0.1:
            defects.append("scratches")
        
        # Dents detection (intensity variations)
        if std_intensity > mean_intensity * 0.2:
            defects.append("dents")
        
        # Color inconsistencies
        if h_uniformity > 2.0 or s_uniformity > 2.0:
            defects.append("color_variation")
        
        # Surface roughness
        if laplacian_var > 1000:
            defects.append("rough_surface")
        
        # Determine overall quality
        quality_score = 1.0 - len(defects) * 0.2
        quality_score = max(0.0, quality_score)
        
        status = "OK" if quality_score >= (1.0 - self.sensitivity) else "NG"
        
        return {
            "status": status,
            "confidence": quality_score,
            "defects": defects,
            "edge_density": edge_density,
            "texture_variance": laplacian_var,
            "intensity_std": std_intensity,
            "color_uniformity": (h_uniformity + s_uniformity + v_uniformity) / 3,
            "reason": ", ".join(defects) if defects else "No defects detected"
        }
    
    def detect_scratches(self, image: np.ndarray, mask: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect scratches in masked region
        
        Args:
            image: Original image
            mask: Binary mask of region to analyze
            
        Returns:
            List of bounding boxes for detected scratches (x, y, w, h)
        """
        # Apply mask
        masked_image = cv2.bitwise_and(image, image, mask=mask.astype(np.uint8))
        gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
        
        # Morphological operations to enhance scratches
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Subtract to find linear features
        scratch_candidates = cv2.absdiff(gray, morph)
        
        # Threshold
        _, thresh = cv2.threshold(scratch_candidates, 30, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        scratches = []
        for contour in contours:
            # Filter by aspect ratio (scratches are long and thin)
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            if aspect_ratio > 5 or aspect_ratio < 0.2:  # Long thin features
                if cv2.contourArea(contour) > 50:  # Minimum size
                    scratches.append((x, y, w, h))
        
        return scratches


class ResultLogger:
    """Logger for saving detection results and images"""
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize result logger
        
        Args:
            output_dir: Directory to save results
        """
        self.output_dir = output_dir
        self.ensure_directories()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def ensure_directories(self):
        """Ensure output directories exist"""
        os.makedirs(os.path.join(self.output_dir, "outputs_ng"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "outputs_ok"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "logs"), exist_ok=True)
    
    def save_detection_result(self, 
                            image: np.ndarray,
                            detection_result: dict,
                            quality_result: dict,
                            save_image: bool = True) -> str:
        """
        Save detection result with image
        
        Args:
            image: Original or processed image
            detection_result: Detection results dict
            quality_result: Quality analysis results dict
            save_image: Whether to save the image
            
        Returns:
            str: Path to saved file
        """
        # Determine output directory based on quality
        status = quality_result.get("status", "NG")
        subdir = "outputs_ok" if status == "OK" else "outputs_ng"
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"detection_{self.session_id}_{timestamp}.jpg"
        filepath = os.path.join(self.output_dir, subdir, filename)
        
        # Save image if requested
        if save_image:
            cv2.imwrite(filepath, image)
        
        # Save metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "filename": filename if save_image else None,
            "detection": detection_result,
            "quality": quality_result
        }
        
        metadata_filename = filename.replace(".jpg", ".json")
        metadata_path = os.path.join(self.output_dir, subdir, metadata_filename)
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved detection result to {filepath}")
        return filepath
    
    def log_session_stats(self, stats: dict):
        """
        Log session statistics
        
        Args:
            stats: Session statistics dict
        """
        log_filename = f"session_stats_{self.session_id}.json"
        log_path = os.path.join(self.output_dir, "logs", log_filename)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stats": stats
        }
        
        # Read existing logs or create new
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs = json.load(f)
            logs.append(log_entry)
        else:
            logs = [log_entry]
        
        with open(log_path, 'w') as f:
            json.dump(logs, f, indent=2)
        
        logger.info(f"Logged session stats to {log_path}")


class ImageProcessor:
    """Main image processing utility combining all processors"""
    
    def __init__(self, pixel_to_mm_ratio: float = 1.0, sensitivity: float = 0.1):
        """
        Initialize image processor
        
        Args:
            pixel_to_mm_ratio: Pixel to millimeter conversion ratio
            sensitivity: Quality analysis sensitivity
        """
        self.roi_manager = ROIManager()
        self.dimension_calculator = DimensionCalculator(pixel_to_mm_ratio)
        self.quality_analyzer = QualityAnalyzer(sensitivity)
        self.result_logger = ResultLogger()
    
    def process_frame(self, 
                     frame: np.ndarray,
                     apply_roi: bool = True) -> np.ndarray:
        """
        Process frame with ROI and preprocessing
        
        Args:
            frame: Input frame
            apply_roi: Whether to apply ROI mask
            
        Returns:
            np.ndarray: Processed frame
        """
        if apply_roi and self.roi_manager.roi_set:
            frame = self.roi_manager.apply_roi(frame)
        
        return frame
    
    def update_calibration(self, pixel_length: float, real_length: float):
        """Update calibration ratio"""
        self.dimension_calculator.set_calibration(pixel_length, real_length)
    
    def set_roi(self, points: List[Tuple[int, int]], image_shape: Tuple[int, int]):
        """Set region of interest"""
        self.roi_manager.set_roi(points, image_shape)
