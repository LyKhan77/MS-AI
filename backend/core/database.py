import os
import json
from datetime import datetime
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.sessions_dir = Config.SESSIONS_DIR
        self._ensure_db()

    def _ensure_db(self):
        # Ensure the directory for db.json exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir: # Only create if db_path includes a directory
            os.makedirs(db_dir, exist_ok=True)
            
        if not os.path.exists(self.db_path):
            self._save_db({"sessions": [], "active_session_id": None})

    def _load_db(self):
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _save_db(self, data):
        # Ensure directory exists before saving
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_session(self, name, max_count):
        db = self._load_db()
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session = {
            "id": session_id,
            "name": name,
            "max_count": max_count,
            "total_count": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "active"
        }
        db["sessions"].append(session)
        db["active_session_id"] = session_id
        self._save_db(db)
        
        # Create session directory
        session_dir = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, 'captures'), exist_ok=True)
        
        return session

    def stop_session(self):
        db = self._load_db()
        if db['active_session_id']:
            # Find and update session
            for session in db['sessions']:
                if session['id'] == db['active_session_id']:
                    session['end_time'] = datetime.now().isoformat()
                    session['status'] = 'completed'
                    break
            
            db['active_session_id'] = None
            self._save_db(db)
            return {"status": "session_stopped"}
        return {"status": "no_active_session"}

    def update_session_count(self, session_id, count):
        db = self._load_db()
        for s in db["sessions"]:
            if s["id"] == session_id:
                s["total_count"] = count
                break
        self._save_db(db)

    def get_all_sessions(self):
        db = self._load_db()
        return db["sessions"]

    def get_session_by_id(self, session_id):
        db = self._load_db()
        for s in db["sessions"]:
            if s["id"] == session_id:
                return s
        return None
    
    def get_active_session(self):
        """Get currently active session"""
        db = self._load_db()
        if db['active_session_id']:
            for session in db['sessions']:
                if session['id'] == db['active_session_id']:
                    return session
        return None
