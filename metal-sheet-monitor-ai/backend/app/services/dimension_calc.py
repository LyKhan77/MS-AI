import cv2
import numpy as np

class DimensionCalculator:
    def __init__(self):
        # Default ratio: 1 pixel = 1 mm (Must be calibrated)
        self.pixel_to_mm_ratio = 1.0 
    
    def set_calibration(self, known_length_mm, pixel_length):
        if pixel_length > 0:
            self.pixel_to_mm_ratio = known_length_mm / pixel_length

    def measure_largest_object(self, image):
        """
        Find largest contour and measure dimensions
        Returns: (width_mm, height_mm, annotated_image)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # Simple threshold - in production might need efficient adaptive method
        # Assuming metal sheet is distinct from background
        _, thresh = cv2.threshold(blur, 50, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return 0, 0, image
            
        # Get largest contour
        c = max(contours, key=cv2.contourArea)
        
        # Rotated Rectangle
        rect = cv2.minAreaRect(c)
        (x, y), (w, h), angle = rect
        
        # Calculate metric dimensions
        width_mm = w * self.pixel_to_mm_ratio
        height_mm = h * self.pixel_to_mm_ratio
        
        # Visualization
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        annotated = image.copy()
        cv2.drawContours(annotated, [box], 0, (0, 0, 255), 2)
        
        # Draw dimensions
        cv2.putText(annotated, f"{width_mm:.1f}mm", (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return width_mm, height_mm, annotated

dimension_service = DimensionCalculator()
