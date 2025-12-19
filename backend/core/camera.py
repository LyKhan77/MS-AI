import cv2
import time
import threading
import os
from config import Config

class Camera:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.is_paused = False
        self.lock = threading.Lock()
        self.source = None  # Don't set default source yet
        self.total_frames = 0
        self.current_frame = 0
        self.last_frame = None  # Cache last frame for pause

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
        
        # Get total frames if it's a video file
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.is_paused = False
            
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
        
        # If paused, return the last cached frame
        if self.is_paused and self.last_frame is not None:
            return True, self.last_frame
            
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.last_frame = frame.copy()  # Cache the frame
        
        if not ret:
            # If video file ends, loop it
            if self.total_frames > 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame = 0
                ret, frame = self.cap.read()
                if ret:
                    self.last_frame = frame.copy()
            else:
                return None, None
            
        return ret, frame
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        print(f"[CAMERA] Resuming playback from frame {self.current_frame}")
        self.is_paused = False
    
    def seek(self, frame_number):
        if self.cap and self.total_frames > 0:
            frame_number = max(0, min(frame_number, self.total_frames - 1))
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
    
    def get_playback_info(self):
        return {
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "is_paused": self.is_paused,
            "fps": int(self.cap.get(cv2.CAP_PROP_FPS)) if self.cap else 0
        }

    def __del__(self):
        self.stop()
