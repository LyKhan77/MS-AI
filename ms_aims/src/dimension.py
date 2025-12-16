class DimensionCalculator:
    def __init__(self, calibration_factor=1.0):
        self.calibration_factor = calibration_factor  # pixels per mm

    def calibrate(self, reference_pixels, known_mm):
        if reference_pixels > 0:
            self.calibration_factor = reference_pixels / known_mm
            return self.calibration_factor
        return None

    def pixels_to_mm(self, pixels):
        return pixels / self.calibration_factor
