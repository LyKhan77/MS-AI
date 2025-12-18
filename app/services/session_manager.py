"""
Session Manager
Coordinates camera, AI, counting logic, and storage
"""

import cv2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from app.services.camera_manager import CameraManager
from app.services.ai_inference import AIInference
from app.services.counting_logic import CountingLogic
from app.services.storage_manager import StorageManager


class SessionManager:
    """Manages counting sessions and coordinates all services"""
    
    def __init__(self, config):
        """
        Initialize session manager
        
        Args:
            config: Flask configuration object
        """
        self.config = config
        
        # Initialize services
        self.camera = CameraManager(rtsp_url=config.RTSP_URL)
        self.ai = AIInference(
            model_path=str(config.YOLO_COUNTING_MODEL),
            device='cuda' if config.USE_GPU else 'cpu',
            conf_threshold=config.DETECTION_CONFIDENCE_THRESHOLD
        )
        self.counting = CountingLogic(
            motion_threshold=25.0,
            stability_frames=5,
            min_detection_confidence=config.DETECTION_CONFIDENCE_THRESHOLD
        )
        self.storage = StorageManager(
            captures_dir=config.CAPTURES_DIR,
            sessions_index_file=config.SESSIONS_INDEX_FILE
        )
        
        # Session state
        self.active_session: Optional[Dict] = None
        self.is_processing = False
        
        print("SessionManager initialized")
    
    def start_session(self, session_name: str, max_count_target: int) -> Dict:
        """
        Start a new counting session
        
        Args:
            session_name: User-friendly session name
            max_count_target: Target count for this session
            
        Returns:
            Session info dict
        """
        if self.active_session:
            raise ValueError("Session already active. Finish current session first.")
        
        # Create session ID (sanitized)
        session_id = "".join(c for c in session_name if c.isalnum() or c in ('_', '-'))
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create session metadata
        session_data = {
            'session_id': session_id,
            'session_name': session_name,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'status': 'active',
            'max_count_target': max_count_target,
            'current_count': 0,
            'alert_triggered': False,
            'alert_type': None,
            'camera_source': {
                'type': self.camera.source_type,
                'url': self.camera.rtsp_url or self.camera.video_file
            },
            'detection_settings': {
                'confidence_threshold': self.config.DETECTION_CONFIDENCE_THRESHOLD,
                'model_name': self.config.YOLO_COUNTING_MODEL.name,
                'model_version': 'v1.0'
            },
            'statistics': {
                'total_captures': 0,
                'avg_detection_confidence': 0.0,
                'duration_seconds': 0
            }
        }
        
        # Create session folder
        self.storage.create_session_folder(session_id)
        
        # Save metadata
        self.storage.save_session_metadata(session_id, session_data)
        
        # Update index
        self.storage.update_sessions_index({
            'session_id': session_id,
            'session_name': session_name,
            'start_time': session_data['start_time'],
            'end_time': None,
            'status': 'active',
            'current_count': 0,
            'max_count_target': max_count_target,
            'alert_triggered': False,
            'folder_path': str(self.config.CAPTURES_DIR / session_id)
        })
        
        # Reset counting logic
        self.counting.reset()
        
        # Set active session
        self.active_session = session_data
        self.is_processing = True
        
        print(f"Session started: {session_name} (ID: {session_id})")
        print(f"Target count: {max_count_target}")
        
        return session_data
    
    def finish_session(self) -> Dict:
        """
        Finish current session
        
        Returns:
            Session summary with alert info
        """
        if not self.active_session:
            raise ValueError("No active session")
        
        session_id = self.active_session['session_id']
        end_time = datetime.now().isoformat()
        
        # Calculate duration
        start = datetime.fromisoformat(self.active_session['start_time'])
        end = datetime.fromisoformat(end_time)
        duration_seconds = (end - start).total_seconds()
        
        # Get final count
        final_count = self.counting.get_current_count()
        target = self.active_session['max_count_target']
        
        # Determine alert
        alert_triggered = False
        alert_type = None
        
        if final_count < target:
            alert_triggered = True
            alert_type = 'under'
        elif final_count > target:
            alert_triggered = True
            alert_type = 'over'
        
        # Update session metadata
        self.active_session['end_time'] = end_time
        self.active_session['status'] = 'completed'
        self.active_session['current_count'] = final_count
        self.active_session['alert_triggered'] = alert_triggered
        self.active_session['alert_type'] = alert_type
        self.active_session['statistics']['duration_seconds'] = duration_seconds
        
        # Save
        self.storage.save_session_metadata(session_id, self.active_session)
        self.storage.update_session_status(session_id, 'completed', end_time)
        
        # Prepare summary
        summary = {
            'session_id': session_id,
            'session_name': self.active_session['session_name'],
            'final_count': final_count,
            'target_count': target,
            'alert_triggered': alert_triggered,
            'alert_type': alert_type,
            'duration_seconds': duration_seconds
        }
        
        print(f"Session finished: {session_id}")
        print(f"  Final count: {final_count} / {target}")
        print(f"  Alert: {alert_type if alert_triggered else 'None'}")
        
        # Clear active session
        self.active_session = None
        self.is_processing = False
        
        return summary
    
    def process_frame_for_counting(self, frame):
        """
        Process frame for counting (called from video streaming loop)
        
        Args:
            frame: Current frame
            
        Returns:
            Annotated frame
        """
        if not self.is_processing or not self.active_session:
            return frame
        
        # Run AI detection
        annotated_frame, detections = self.ai.detect_and_draw(frame)
        
        # Process through counting logic
        count_event = self.counting.process_frame(frame, detections)
        
        # If count event occurred, save capture
        if count_event:
            self._handle_count_event(count_event)
        
        # Draw count overlay
        annotated_frame = self._draw_count_overlay(annotated_frame)
        
        return annotated_frame
    
    def _handle_count_event(self, count_event: Dict):
        """Handle count event (save capture, log)"""
        session_id = self.active_session['session_id']
        capture_id = self.storage.get_next_capture_id(session_id)
        
        # Save image
        filename = f"img_{capture_id:03d}.jpg"
        session_folder = self.config.CAPTURES_DIR / session_id
        filepath = session_folder / filename
        
        cv2.imwrite(str(filepath), count_event['frame'])
        
        # Create detection log entry
        detection_log = {
            'capture_id': capture_id,
            'timestamp': count_event['timestamp'],
            'filename': filename,
            'detection': {
                'confidence': count_event['detection']['confidence'],
                'bbox': count_event['detection']['bbox'],
                'class_name': count_event['detection']['class_name'],
                'class_id': count_event['detection']['class_id']
            },
            'frame_info': {
                'frame_number': self.camera.frame_count if self.camera else 0,
                'fps': self.camera.fps if self.camera else 0
            },
            'defect_analysis': None  # For Phase 2
        }
        
        # Save to log
        self.storage.append_detection_log(session_id, detection_log)
        
        # Update session metadata
        self.active_session['current_count'] = count_event['count']
        self.active_session['statistics']['total_captures'] = capture_id
        self.storage.save_session_metadata(session_id, self.active_session)
        
        print(f"Capture saved: {filename}")
    
    def _draw_count_overlay(self, frame):
        """Draw count information on frame"""
        if not self.active_session:
            return frame
        
        current_count = self.counting.get_current_count()
        target = self.active_session['max_count_target']
        state = self.counting.get_state()
        
        # Draw semi-transparent overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Top bar
        cv2.rectangle(overlay, (0, 0), (w, 80), (10, 14, 26), -1)  # Dark bg
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Count text (large)
        count_text = f"{current_count} / {target}"
        cv2.putText(
            frame,
            count_text,
            (20, 55),
            cv2.FONT_HERSHEY_BOLD,
            1.8,
            (115, 52, 0),  # Primary color
            3
        )
        
        # State text
        state_text = f"State: {state}"
        cv2.putText(
            frame,
            state_text,
            (w - 300, 55),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (228, 232, 240),  # Light text
            2
        )
        
        return frame
    
    def get_session_status(self) -> Optional[Dict]:
        """Get current session status"""
        if not self.active_session:
            return None
        
        return {
            'active': True,
            'session_id': self.active_session['session_id'],
            'session_name': self.active_session['session_name'],
            'current_count': self.counting.get_current_count(),
            'max_count_target': self.active_session['max_count_target'],
            'start_time': self.active_session['start_time'],
            'state': self.counting.get_state()
        }
    
    def initialize_services(self) -> bool:
        """Initialize all services (call on app startup)"""
        success = True
        
        # Start camera  
        if not self.camera.start():
            print("Warning: Camera failed to start")
            success = False
        
        # Load AI model
        if not self.ai.load_model():
            print("Warning: AI model failed to load")
            success = False
        
        return success
    
    def shutdown(self):
        """Shutdown all services"""
        print("Shutting down SessionManager...")
        
        if self.active_session:
            try:
                self.finish_session()
            except:
                pass
        
        self.camera.stop()
        self.ai.unload_model()
        
        print("SessionManager shutdown complete")
