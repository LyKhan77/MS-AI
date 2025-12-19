import json
import os
import time
from backend.config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DB_PATH
        self.sessions_dir = Config.SESSIONS_DIR
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(self.db_path):
            self._save_db({"sessions": [], "active_session_id": None})

    def _load_db(self):
        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _save_db(self, data):
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=4)

    def create_session(self, name, max_count):
        db = self._load_db()
        session_id = str(int(time.time()))
        
        session_folder = os.path.join(self.sessions_dir, session_id)
        os.makedirs(session_folder, exist_ok=True)
        
        # Create 'captures' and 'defects' subfolders
        os.makedirs(os.path.join(session_folder, 'captures'), exist_ok=True)
        os.makedirs(os.path.join(session_folder, 'defects'), exist_ok=True)

        new_session = {
            "id": session_id,
            "name": name,
            "max_count": max_count,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "total_count": 0,
            "calibration_factor": Config.PIXEL_TO_MM_DEFAULT
        }
        
        db["sessions"].append(new_session)
        db["active_session_id"] = session_id
        self._save_db(db)
        return new_session

    def get_active_session(self):
        db = self._load_db()
        active_id = db.get("active_session_id")
        if not active_id:
            return None
        for s in db["sessions"]:
            if s["id"] == active_id:
                return s
        return None

    def stop_session(self):
        db = self._load_db()
        active_id = db.get("active_session_id")
        if active_id:
            for s in db["sessions"]:
                if s["id"] == active_id:
                    s["status"] = "completed"
                    break
        db["active_session_id"] = None
        self._save_db(db)
        return {"status": "stopped"}

    def update_count(self, session_id, count):
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
