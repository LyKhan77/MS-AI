"""
Camera Manager
Handles RTSP stream and video file capture with thread-safe operations
"""

import cv2
import threading
import time
from typing import Optional, Tuple
import numpy as np
from pathlib import Path


class CameraManager:
    """Thread-safe camera manager for RTSP and video file sources"""
    
    def __init__(self, rtsp_url: str = None, video_file: str = None):
        """
        Initialize camera manager
        
        Args:
            rtsp_url: RTSP stream URL
            video_file: Path to video file (for testing)
        """
        self.rtsp_url = rtsp_url
        self.video_file = video_file
        self.source_type = 'rtsp' if rtsp_url else 'file' if video_file else None
        
        # Video capture object
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame = None
        self.ret = False
        self.is_running = False
        
        # Threading
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
        
        # Stats
        self.fps = 0
        self.frame_count = 0
        self.width = 0
        self.height = 0
        
        # Reconnection
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2  # seconds
    
    def start(self) -> bool:
        """
        Start camera capture
        
        Returns:
            True if started successfully
        """
        if self.is_running:
            print("Camera already running")
            return True
        
        # Determine source
        source = self.rtsp_url if self.rtsp_url else self.video_file
        if not source:
            print("No camera source specified")
            return False
        
        # Open video capture
        print(f"Opening camera source: {source[:50]}...")
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            print(f"Failed to open camera source: {source}")
            return False
        
        # Get properties
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 25
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Camera opened successfully")
        print(f"  Resolution: {self.width}x{self.height}")
        print(f"  FPS: {self.fps}")
        
        # Start capture thread
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
        return True
    
    def _capture_loop(self):
        """Background thread for continuous frame capture"""
        reconnect_attempts = 0
        
        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                # Attempt reconnection
                if reconnect_attempts < self.max_reconnect_attempts:
                    print(f"Attempting reconnection... ({reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                    source = self.rtsp_url if self.rtsp_url else self.video_file
                    self.cap = cv2.VideoCapture(source)
                    reconnect_attempts += 1
                    time.sleep(self.reconnect_delay)
                    continue
                else:
                    print("Max reconnection attempts reached. Stopping camera.")
                    self.is_running = False
                    break
            
            # Read frame
            ret, frame = self.cap.read()
            
            if ret:
                with self.lock:
                    self.ret = True
                    self.frame = frame.copy()
                    self.frame_count += 1
                reconnect_attempts = 0  # Reset on successful read
            else:
                with self.lock:
                    self.ret = False
                print("Frame read failed")
                time.sleep(0.1)
        
        # Cleanup
        if self.cap:
            self.cap.release()
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read latest frame (thread-safe)
        
        Returns:
            (success, frame)
        """
        with self.lock:
            return self.ret, self.frame.copy() if self.frame is not None else None
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Get latest frame (convenience method)
        
        Returns:
            Frame or None
        """
        ret, frame = self.read()
        return frame if ret else None
    
    def stop(self):
        """Stop camera capture"""
        print("Stopping camera...")
        self.is_running = False
        
        if self.thread:
            self.thread.join(timeout=5.0)
        
        if self.cap:
            self.cap.release()
        
        print("Camera stopped")
    
    def set_rtsp_url(self, rtsp_url: str) -> bool:
        """
        Change RTSP URL (restart required)
        
        Args:
            rtsp_url: New RTSP URL
            
        Returns:
            True if changed successfully
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.rtsp_url = rtsp_url
        self.source_type = 'rtsp'
        
        if was_running:
            return self.start()
        
        return True
    
    def set_video_file(self, video_file: str) -> bool:
        """
        Change to video file source
        
        Args:
            video_file: Path to video file
            
        Returns:
            True if changed successfully
        """
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.video_file = video_file
        self.source_type = 'file'
        
        if was_running:
            return self.start()
        
        return True
    
    def is_opened(self) -> bool:
        """Check if camera is opened and running"""
        return self.is_running and self.ret
    
    def get_stats(self) -> dict:
        """
        Get camera statistics
        
        Returns:
            Dict with stats
        """
        return {
            'is_running': self.is_running,
            'is_opened': self.is_opened(),
            'source_type': self.source_type,
            'fps': self.fps,
            'width': self.width,
            'height': self.height,
            'frame_count': self.frame_count
        }
    
    def save_frame(self, filepath: str) -> bool:
        """
        Save current frame to file
        
        Args:
            filepath: Output file path
            
        Returns:
            True if saved successfully
        """
        frame = self.get_frame()
        if frame is None:
            return False
        
        try:
            cv2.imwrite(filepath, frame)
            return True
        except Exception as e:
            print(f"Error saving frame: {e}")
            return False
