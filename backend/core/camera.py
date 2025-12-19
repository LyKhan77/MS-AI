import cv2
import time
import threading
from config import Config

class Camera:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.lock = threading.Lock()
        self.source = None  # Don't set default source yet

    def set_source(self, source):
        """
        Switch between RTSP URL (string/int) and Video File path.
        """
        with self.lock:
            self.stop()
            # Expand ~ to home directory for file paths
            if isinstance(source, str):
                source = os.path.expanduser(source)
                # If source is a digit string, convert to int for webcam
                if source.isdigit():
                    source = int(source)
            self.source = source
            self.start()

    def start(self):
        if self.is_running:
            return
        
        # Initialize capture
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print(f"Error: Could not open source {self.source}")
            return
            
        self.is_running = True
        print(f"Camera started with source: {self.source}")

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def get_frame(self):
        if not self.is_running or self.cap is None:
            return None, None
            
        ret, frame = self.cap.read()
        if not ret:
            # If video file ends, loop it or stop? Let's loop for now if it's a file
            # But usually for QC, we might want it to stop. 
            # For simplicity in 'Stream' mode, we might restart or just return None.
            # If it is a file, verify logic. user said 'Input Video by browse local files'.
            # We will handle looping in the main loop if needed, here just return None.
            return None, None
            
        return ret, frame

    def __del__(self):
        self.stop()
