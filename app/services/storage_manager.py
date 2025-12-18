"""
JSON Storage Manager
Handles all JSON file operations for session data storage
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import shutil


class StorageManager:
    """Manager for JSON-based storage operations"""
    
    def __init__(self, captures_dir: Path, sessions_index_file: Path):
        """
       Initialize storage manager
        
        Args:
            captures_dir: Directory for captured images and session data
            sessions_index_file: Path to sessions_index.json
        """
        self.captures_dir = Path(captures_dir)
        self.sessions_index_file = Path(sessions_index_file)
        
        # Ensure directories exist
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sessions index if not exists
        if not self.sessions_index_file.exists():
            self._create_sessions_index()
    
    def _create_sessions_index(self):
        """Create empty sessions index file"""
        initial_data = {
            "sessions": [],
            "last_updated": None
        }
        with open(self.sessions_index_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    # ============================================
    # Session Index Operations
    # ============================================
    
    def get_sessions_index(self) -> Dict:
        """Load sessions index"""
        try:
            with open(self.sessions_index_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._create_sessions_index()
            return {"sessions": [], "last_updated": None}
    
    def update_sessions_index(self, session_data: Dict) -> None:
        """
        Update or add session to index
        
        Args:
            session_data: Session metadata dict
        """
        index = self.get_sessions_index()
        
        # Check if session already exists
        existing_idx = None
        for idx, session in enumerate(index['sessions']):
            if session['session_id'] == session_data['session_id']:
                existing_idx = idx
                break
        
        # Update or append
        if existing_idx is not None:
            index['sessions'][existing_idx] = session_data
        else:
            index['sessions'].append(session_data)
        
        # Update timestamp
        index['last_updated'] = datetime.now().isoformat()
        
        # Save
        with open(self.sessions_index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def list_all_sessions(self) -> List[Dict]:
        """Get list of all sessions"""
        index = self.get_sessions_index()
        return index['sessions']
    
    # ============================================
    # Session Management
    # ============================================
    
    def create_session_folder(self, session_id: str) -> str:
        """
        Create folder for session
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path to created session folder
        """
        # Sanitize session_id for folder name
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        session_folder = self.captures_dir / safe_id
        session_folder.mkdir(parents=True, exist_ok=True)
        return str(session_folder)
    
    def save_session_metadata(self, session_id: str, metadata: Dict) -> None:
        """
        Save session metadata to JSON file
        
        Args:
            session_id: Session identifier
            metadata: Session metadata dict
        """
        session_folder = self.create_session_folder(session_id)
        metadata_file = Path(session_folder) / 'session_metadata.json'
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_session_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Load session metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session metadata dict or None if not found
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        metadata_file = self.captures_dir / safe_id / 'session_metadata.json'
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    def update_session_status(self, session_id: str, status: str, end_time: str = None) -> None:
        """
        Update session status
        
        Args:
            session_id: Session identifier
            status: New status ('active', 'completed', 'cancelled')
            end_time: Optional end timestamp
        """
        metadata = self.load_session_metadata(session_id)
        if metadata:
            metadata['status'] = status
            if end_time:
                metadata['end_time'] = end_time
            self.save_session_metadata(session_id, metadata)
            
            # Update index
            self.update_sessions_index({
                'session_id': session_id,
                'session_name': metadata.get('session_name'),
                'start_time': metadata.get('start_time'),
                'end_time': metadata.get('end_time'),
                'status': status,
                'current_count': metadata.get('current_count', 0),
                'max_count_target': metadata.get('max_count_target', 0),
                'alert_triggered': metadata.get('alert_triggered', False),
                'folder_path': str(self.captures_dir / session_id)
            })
    
    # ============================================
    # Detection Log Operations
    # ============================================
    
    def append_detection_log(self, session_id: str, detection_data: Dict) -> None:
        """
        Append detection data to log
        
        Args:
            session_id: Session identifier
            detection_data: Detection data dict
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        session_folder = self.captures_dir / safe_id
        log_file = session_folder / 'detections_log.json'
        
        # Load existing log or create new
        if log_file.exists():
            with open(log_file, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {
                'session_id': session_id,
                'captures': []
            }
        
        # Append new detection
        log_data['captures'].append(detection_data)
        
        # Save
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def load_detection_logs(self, session_id: str) -> Dict:
        """
        Load detection logs
        
        Args:
            session_id: Session identifier
            
        Returns:
            Detection logs dict
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        log_file = self.captures_dir / safe_id / 'detections_log.json'
        
        if not log_file.exists():
            return {'session_id': session_id, 'captures': []}
        
        with open(log_file, 'r') as f:
            return json.load(f)
    
    def update_detection_defect_analysis(self, session_id: str, capture_id: int, defect_data: Dict) -> None:
        """
        Update detection with defect analysis results (Phase 2)
        
        Args:
            session_id: Session identifier
            capture_id: Capture ID
            defect_data: Defect analysis data
        """
        logs = self.load_detection_logs(session_id)
        
        # Find capture by ID
        for capture in logs['captures']:
            if capture['capture_id'] == capture_id:
                capture['defect_analysis'] = defect_data
                break
        
        # Save updated logs
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        log_file = self.captures_dir / safe_id / 'detections_log.json'
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def update_detection_measurement(self, session_id: str, capture_id: int, measurement_data: Dict) -> None:
        """
        Update detection with dimension measurement (Phase 3)
        
        Args:
            session_id: Session identifier
            capture_id: Capture ID
            measurement_data: Measurement data
        """
        logs = self.load_detection_logs(session_id)
        
        # Find capture by ID
        for capture in logs['captures']:
            if capture['capture_id'] == capture_id:
                capture['dimension_measurement'] = measurement_data
                break
        
        # Save updated logs
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        log_file = self.captures_dir / safe_id / 'detections_log.json'
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    # ============================================
    # Utility Functions
    # ============================================
    
    def get_session_images(self, session_id: str) -> List[str]:
        """
        Get list of image files in session folder
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of image filenames
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        session_folder = self.captures_dir / safe_id
        
        if not session_folder.exists():
            return []
        
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            images.extend([f.name for f in session_folder.glob(ext)])
        
        return sorted(images)
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete session folder and data
        
        Args:
            session_id: Session identifier
        """
        safe_id = "".join(c for c in session_id if c.isalnum() or c in ('_', '-'))
        session_folder = self.captures_dir / safe_id
        
        if session_folder.exists():
            shutil.rmtree(session_folder)
        
        # Remove from index
        index = self.get_sessions_index()
        index['sessions'] = [s for s in index['sessions'] if s['session_id'] != session_id]
        index['last_updated'] = datetime.now().isoformat()
        
        with open(self.sessions_index_file, 'w') as f:
            json.dump(index, f, indent=2)
    
    def get_next_capture_id(self, session_id: str) -> int:
        """
        Get next capture ID for session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Next capture ID
        """
        logs = self.load_detection_logs(session_id)
        if not logs['captures']:
            return 1
        return max([c['capture_id'] for c in logs['captures']]) + 1
