"""
Counting Logic - State Machine for Metal Sheet Counting  
Implements the stacking flow detection logic
"""

import cv2
import numpy as np
from typing import Optional, List, Dict
from enum import Enum
from datetime import datetime


class CountingState(Enum):
    """Counting states"""
    EMPTY_STABLE = 0  # Empty or stable baseline
    MOTION_DETECTED = 1  # Motion/occlusion detected
    NEW_OBJECT = 2  # New object stable
    VERIFIED = 3  # Object verified with AI


class CountingLogic:
    """
    State machine for counting metal sheets during stacking
    
    Workflow:
        State 0 (EMPTY_STABLE): Baseline stable image
        State 1 (MOTION_DETECTED): Hand/object enters frame (occlusion)
        State 2 (NEW_OBJECT): Hand exits, new stable image
        State 3 (VERIFIED): AI confirms metal sheet presence → COUNT +1
    """
    
    def __init__(self, 
                 motion_threshold: float = 25.0,
                 stability_frames: int = 5,
                 min_detection_confidence: float = 0.8,
                 cooldown_frames: int = 10):
        """
        Initialize counting logic
        
        Args:
            motion_threshold: Motion detection threshold
            stability_frames: Frames to wait for stability
            min_detection_confidence: Minimum AI confidence for counting
            cooldown_frames: Frames to wait before next count
        """
        self.motion_threshold = motion_threshold
        self.stability_frames = stability_frames
        self.min_detection_confidence = min_detection_confidence
        self.cooldown_frames = cooldown_frames
        
        # State
        self.current_state = CountingState.EMPTY_STABLE
        self.previous_frame: Optional[np.ndarray] = None
        self.baseline_frame: Optional[np.ndarray] = None
        
        # Counters
        self.stability_counter = 0
        self.cooldown_counter = 0
        
        # Statistics
        self.total_motion_events = 0
        self.total_counts = 0
        self.false_positives = 0
        
        print("Counting Logic initialized")
        print(f"  Motion threshold: {motion_threshold}")
        print(f"  Stability frames: {stability_frames}")
        print(f"  Min confidence: {min_detection_confidence}")
    
    def reset(self):
        """Reset state machine"""
        self.current_state = CountingState.EMPTY_STABLE
        self.previous_frame = None
        self.baseline_frame = None
        self.stability_counter = 0
        self.cooldown_counter = 0
        print("Counting logic reset")
    
    def _calculate_frame_diff(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Calculate difference between two frames
        
        Args:
            frame1: First frame
            frame2: Second frame
            
        Returns:
            Mean absolute difference
        """
        # Convert to grayscale
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        # Calculate absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Apply Gaussian blur to reduce noise
        diff = cv2.GaussianBlur(diff, (5, 5), 0)
        
        # Calculate mean difference
        mean_diff = np.mean(diff)
        
        return mean_diff
    
    def _is_motion_detected(self, current_frame: np.ndarray) -> bool:
        """
        Detect if there is significant motion
        
        Args:
            current_frame: Current frame
            
        Returns:
            True if motion detected
        """
        if self.previous_frame is None:
            return False
        
        diff = self._calculate_frame_diff(self.previous_frame, current_frame)
        return diff > self.motion_threshold
    
    def _is_stable(self, current_frame: np.ndarray) -> bool:
        """
        Check if frame is stable (no motion for N frames)
        
        Args:
            current_frame: Current frame
            
        Returns:
            True if stable
        """
        if self._is_motion_detected(current_frame):
            self.stability_counter = 0
            return False
        
        self.stability_counter += 1
        return self.stability_counter >= self.stability_frames
    
    def process_frame(self, frame: np.ndarray, detections: List[Dict]) -> Optional[Dict]:
        """
        Process frame through state machine
        
        Args:
            frame: Current frame (BGR)
            detections: AI detections from inference
            
        Returns:
            Dict with count event info if counted, None otherwise
        """
        # Cooldown check
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            self.previous_frame = frame.copy()
            return None
        
        count_event = None
        
        # State machine logic
        if self.current_state == CountingState.EMPTY_STABLE:
            # State 0: Waiting for motion
            if self.baseline_frame is None:
                self.baseline_frame = frame.copy()
            
            if self._is_motion_detected(frame):
                self.current_state = CountingState.MOTION_DETECTED
                self.total_motion_events += 1
                self.stability_counter = 0
                print("State: MOTION_DETECTED")
        
        elif self.current_state == CountingState.MOTION_DETECTED:
            # State 1: Motion detected, waiting for stabilization
            if self._is_stable(frame):
                self.current_state = CountingState.NEW_OBJECT
                print("State: NEW_OBJECT (stable)")
        
        elif self.current_state == CountingState.NEW_OBJECT:
            # State 2: Check for new object with AI
            if len(detections) > 0:
                # Check if detection meets confidence threshold
                highest_conf = max([d['confidence'] for d in detections])
                
                if highest_conf >= self.min_detection_confidence:
                    self.current_state = CountingState.VERIFIED
                    print(f"State: VERIFIED (conf: {highest_conf:.2f})")
                else:
                    print(f"Low confidence: {highest_conf:.2f}, resetting")
                    self.false_positives += 1
                    self.current_state = CountingState.EMPTY_STABLE
            else:
                # No detection, might be false motion
                print("No detection, resetting")
                self.false_positives += 1
                self.current_state = CountingState.EMPTY_STABLE
        
        elif self.current_state == CountingState.VERIFIED:
            # State 3: Count confirmed!
            self.total_counts += 1
            
            # Get best detection
            best_detection = max(detections, key=lambda d: d['confidence'])
            
            count_event = {
                'timestamp': datetime.now().isoformat(),
                'count': self.total_counts,
                'detection': best_detection,
                'frame': frame.copy()
            }
            
            print(f"✓ COUNT: {self.total_counts}")
            
            # Reset to baseline
            self.baseline_frame = frame.copy()
            self.current_state = CountingState.EMPTY_STABLE
            self.stability_counter = 0
            self.cooldown_counter = self.cooldown_frames
        
        # Update previous frame
        self.previous_frame = frame.copy()
        
        return count_event
    
    def get_current_count(self) -> int:
        """Get current count"""
        return self.total_counts
    
    def get_state(self) -> str:
        """Get current state name"""
        return self.current_state.name
    
    def get_stats(self) -> Dict:
        """
        Get counting statistics
        
        Returns:
            Stats dict
        """
        return {
            'current_state': self.current_state.name,
            'total_counts': self.total_counts,
            'motion_events': self.total_motion_events,
            'false_positives': self.false_positives,
            'accuracy': (
                (self.total_counts / self.total_motion_events * 100) 
                if self.total_motion_events > 0 else 0
            )
        }
