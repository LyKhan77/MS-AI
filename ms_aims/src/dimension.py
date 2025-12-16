import cv2
import numpy as np

class DimensionCalculator:
    def __init__(self, calibration_factor=None):
        # pixels per mm. If None, system is uncalibrated.
        # Example: if 100 pixels = 10mm, factor is 10.0
        self.calibration_factor = calibration_factor 

    def set_calibration(self, pixel_length, known_mm):
        """
        Calculate and set the calibration factor based on a reference object.
        """
        if pixel_length > 0 and known_mm > 0:
            self.calibration_factor = pixel_length / known_mm
            print(f"Calibration set: {self.calibration_factor:.2f} px/mm")
            return self.calibration_factor
        return None

    def pixels_to_mm(self, pixels):
        """Convert pixel value to millimeters."""
        if self.calibration_factor:
            return pixels / self.calibration_factor
        return 0.0

    def measure_contour(self, contour):
        """
        Calculate the rotated bounding box dimensions of a contour.
        Returns: (width_mm, height_mm, box_points)
        """
        # Get rotated rectangle
        rect = cv2.minAreaRect(contour)
        (center), (width_px, height_px), angle = rect
        
        # Sort so width is always the longer side (optional convention)
        if width_px < height_px:
            width_px, height_px = height_px, width_px
            
        box_points = cv2.boxPoints(rect)
        box_points = np.int0(box_points)

        width_mm = self.pixels_to_mm(width_px)
        height_mm = self.pixels_to_mm(height_px)
        
        return width_mm, height_mm, box_points
