"""
Video streaming module for handling various input sources
Supports RTSP streams, USB cameras, and video files with threading
"""

import cv2
import numpy as np
import threading
import queue
import time
from typing import Optional, Tuple, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class InputSource(Enum):
    """Enumeration of supported input sources"""
    RTSP = "rtsp"
    USB = "usb"
    FILE = "file"


class VideoStreamer:
    """Threaded video streamer supporting multiple input sources"""
    
    def __init__(self, buffer_size: int = 10):
        """
        Initialize video streamer
        
        Args:
            buffer_size: Maximum number of frames to buffer
        """
        self.buffer_size = buffer_size
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.running = False
        self.thread = None
        self.cap = None
        self.source_type = None
        self.source = None
        self.last_frame_time = 0
        self.fps = 0
        self.frame_count = 0
        self.total_frames = 0
        self.width = 0
        self.height = 0
        
        # Reconnection parameters
        self.reconnect_interval = 5.0  # seconds
        self.max_reconnect_attempts = 5
        self.reconnect_attempts = 0
        
    def connect(self, source: Union[str, int], input_type: InputSource) -> bool:
        """
        Connect to video source
        
        Args:
            source: Video source path (RTSP URL, file path, or camera index)
            input_type: Type of input source
            
        Returns:
            bool: True if connection successful
        """
        try:
            if input_type == InputSource.FILE:
                self.cap = cv2.VideoCapture(source)
                if not self.cap.isOpened():
                    logger.error(f"Failed to open video file: {source}")
                    return False
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
            else:  # RTSP or USB
                # Configure capture for RTSP if needed
                if input_type == InputSource.RTSP:
                    # Optimize for RTSP streaming with Jetson acceleration
                    # Try GStreamer first (Jetson optimized)
                    try:
                        gstreamer_pipeline = (
                            f"rtspsrc location={source} latency=0 ! "
                            "rtph264depay ! h264parse ! nvv4l2decoder ! "
                            "nvvidconv ! video/x-raw,format=BGRx ! "
                            "videoconvert ! video/x-raw,format=BGR ! appsink"
                        )
                        self.cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
                        if self.cap.isOpened():
                            logger.info("Using GStreamer with hardware acceleration")
                        else:
                            raise Exception("GStreamer failed")
                    except:
                        # Fallback to FFmpeg
                        logger.warning("GStreamer failed, using FFmpeg fallback")
                        self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    
                    if self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for real-time
                        self.cap.set(cv2.CAP_PROP_FPS, 30)
                else:  # USB
                    self.cap = cv2.VideoCapture(source)
                
                if not self.cap.isOpened():
                    logger.error(f"Failed to open camera: {source}")
                    return False
            
            # Get video properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.source_type = input_type
            self.source = source
            self.reconnect_attempts = 0
            
            logger.info(f"Connected to {input_type.value} source: {source}")
            logger.info(f"Resolution: {self.width}x{self.height}, FPS: {self.fps}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to video source: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start video streaming thread
        
        Returns:
            bool: True if streaming started successfully
        """
        if self.cap is None or not self.cap.isOpened():
            logger.error("No video source connected")
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._stream_frames, daemon=True)
        self.thread.start()
        logger.info("Video streaming started")
        return True
    
    def stop(self):
        """Stop video streaming"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        logger.info("Video streaming stopped")
    
    def _stream_frames(self):
        """Main streaming loop running in separate thread"""
        while self.running:
            try:
                if self.source_type == InputSource.FILE and self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.total_frames - 1:
                    # Loop video file
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    logger.debug("Video file looped")
                
                ret, frame = self.cap.read()
                
                if not ret:
                    if self.source_type == InputSource.FILE:
                        # End of file, loop
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        # Camera disconnected, try to reconnect
                        self._attempt_reconnect()
                        continue
                
                # Calculate FPS
                current_time = time.time()
                if self.last_frame_time > 0:
                    frame_time = current_time - self.last_frame_time
                    if frame_time > 0:
                        self.fps = 1.0 / frame_time
                self.last_frame_time = current_time
                
                self.frame_count += 1
                
                # Add frame to queue (non-blocking)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Remove oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in streaming loop: {e}")
                if self.source_type != InputSource.FILE:
                    self._attempt_reconnect()
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to video source"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.running = False
            return
        
        logger.warning(f"Attempting reconnection {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}")
        
        # Close current connection
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Wait before reconnecting
        time.sleep(self.reconnect_interval)
        
        # Attempt to reconnect
        if self.connect(self.source, self.source_type):
            self.reconnect_attempts = 0
            logger.info("Reconnection successful")
        else:
            self.reconnect_attempts += 1
            if self.reconnect_attempts < self.max_reconnect_attempts:
                logger.warning(f"Reconnection failed, will retry in {self.reconnect_interval} seconds")
    
    def get_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get latest frame from queue
        
        Args:
            timeout: Maximum time to wait for frame
            
        Returns:
            numpy.ndarray or None: Latest frame or None if no frame available
        """
        try:
            return self.frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """
        Get only the latest frame, clearing old frames
        
        Returns:
            numpy.ndarray or None: Latest frame or None if no frame available
        """
        frame = None
        while True:
            try:
                frame = self.frame_queue.get_nowait()
            except queue.Empty:
                break
        return frame
    
    def is_streaming(self) -> bool:
        """Check if streamer is actively streaming"""
        return self.running and (self.thread is not None and self.thread.is_alive())
    
    def get_info(self) -> dict:
        """Get streamer information"""
        return {
            "source": self.source,
            "source_type": self.source_type.value if self.source_type else None,
            "resolution": (self.width, self.height),
            "fps": self.fps,
            "frame_count": self.frame_count,
            "total_frames": self.total_frames,
            "streaming": self.is_streaming(),
            "queue_size": self.frame_queue.qsize(),
            "buffer_size": self.buffer_size
        }


class MotionDetector:
    """Motion detection using frame difference"""
    
    def __init__(self, threshold: float = 0.05, history_size: int = 5):
        """
        Initialize motion detector
        
        Args:
            threshold: Motion threshold (0.0-1.0)
            history_size: Number of frames to keep in history
        """
        self.threshold = threshold
        self.history_size = history_size
        self.frame_history = []
        self.last_motion_time = 0
        
    def update(self, frame: np.ndarray) -> bool:
        """
        Update motion detector with new frame
        
        Args:
            frame: Input frame
            
        Returns:
            bool: True if motion detected
        """
        if len(self.frame_history) == 0:
            self.frame_history.append(frame.copy())
            return False
        
        # Calculate frame difference
        prev_frame = self.frame_history[-1]
        diff = cv2.absdiff(frame, prev_frame)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        
        # Calculate percentage of changed pixels
        changed_pixels = np.sum(diff_gray > 30)  # Threshold for noise
        total_pixels = diff_gray.size
        change_ratio = changed_pixels / total_pixels
        
        # Update history
        self.frame_history.append(frame.copy())
        if len(self.frame_history) > self.history_size:
            self.frame_history.pop(0)
        
        # Check if motion detected
        if change_ratio > self.threshold:
            self.last_motion_time = time.time()
            return True
        
        # Check if scene is stable (no motion for 1 second)
        stable_duration = time.time() - self.last_motion_time
        return stable_duration >= 1.0 and change_ratio <= self.threshold
    
    def is_stable(self) -> bool:
        """Check if scene is stable (no recent motion)"""
        stable_duration = time.time() - self.last_motion_time
        return stable_duration >= 1.0
