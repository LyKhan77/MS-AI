import cv2
import threading
import time
import logging
import os
from typing import Optional, Tuple, Union

logger = logging.getLogger(__name__)

class CameraManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CameraManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        self.source_type = "rtsp"  # "rtsp" or "file"
        self.source_path: Union[str, int] = 0 # Default to webcam 0 if nothing specified
        self.cap: Optional[cv2.VideoCapture] = None
        
        self.lock = threading.Lock()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        self.current_frame = None
        self.last_frame_time = 0
        
        # Loop control for video files
        self.loop_video = True
        
        self.initialized = True

    def set_source(self, source_type: str, source_path: str):
        """
        Set the video source.
        source_type: 'rtsp' or 'file'
        source_path: rtsp url or file path
        """
        with self.lock:
            self.stop()
            self.source_type = source_type
            self.source_path = source_path
            logger.info(f"Camera source set to: {self.source_type} - {self.source_path}")

    def start(self):
        with self.lock:
            if self.running:
                logger.warning("Camera is already running")
                return

            logger.info(f"Starting camera/video stream from {self.source_path}")
            
            # Open VideoCapture
            if self.source_type == "rtsp":
                # RTSP usually requires specific backend or options for low latency
                # For basic cv2:
                self.cap = cv2.VideoCapture(self.source_path)
            else:
                # Video file
                if not os.path.exists(str(self.source_path)) and not str(self.source_path).isdigit():
                     logger.error(f"File not found: {self.source_path}")
                     # Fallback to test if it's just a test
                self.cap = cv2.VideoCapture(self.source_path)

            if not self.cap or not self.cap.isOpened():
                logger.error("Failed to open video source")
                # Don't raise error, just return, maybe set status error
                return

            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()

    def stop(self):
        with self.lock:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1.0)
                self.thread = None
            
            if self.cap:
                self.cap.release()
                self.cap = None
            logger.info("Camera stream stopped")

    def _update(self):
        """
        Thread target to continuously read frames
        """
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                if self.source_type == "file" and self.loop_video:
                    # Reset video to beginning
                    logger.info("Video ended, looping...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning("Failed to read frame or stream ended")
                    self.running = False
                    break
            
            # Update current frame
            with self.lock:
                self.current_frame = frame.copy()
                self.last_frame_time = time.time()
            
            # Control FPS for video files to not play too fast
            if self.source_type == "file":
                time.sleep(0.03) # Approx 30 FPS cap
            else:
                # For RTSP, we read as fast as possible to clear buffer
                pass
                
    def get_frame(self):
        """
        Return the latest frame
        """
        with self.lock:
            return self.current_frame

# Global Instance
camera_manager = CameraManager()
