from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import cv2
import base64
import time
import threading
import os

from config import Config
from core.database import Database
from core.camera import Camera
from core.detector import MetalSheetCounter
from core.analyzer import SheetAnalyzer

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Cores
db = Database()
camera = Camera()
detector = MetalSheetCounter()
analyzer = SheetAnalyzer()

# Global state for the streaming thread
streaming_thread = None
stop_streaming = threading.Event()

def generate_frames():
    """
    Background thread function to capture frames, run, and emit to SocketIO
    """
    camera.start()
    while not stop_streaming.is_set():
        ret, frame = camera.get_frame()
        if not ret:
            time.sleep(0.1)
            continue

        # Run YOLO Detector
        count, debug_frame = detector.process(frame)
        
        # Prepare frame for streaming (JPEG -> Base64)
        # Use debug_frame (with bounding boxes) if available
        final_frame = debug_frame if debug_frame is not None else frame
        _, buffer = cv2.imencode('.jpg', final_frame)
        frame_bytes = base64.b64encode(buffer).decode('utf-8')
        
        # Emit to client
        socketio.emit('video_frame', {'image': frame_bytes, 'count': detector.get_count()})
        
        socketio.sleep(1 / Config.FRAME_RATE) 
    
    camera.stop()

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "running"})

@app.route('/api/session/start', methods=['POST'])
def start_session():
    data = request.json
    name = data.get('name', 'Untitled')
    max_count = data.get('max_count', 100)
    session = db.create_session(name, max_count)
    
    # Configure Detector for this session
    session_dir = os.path.join(Config.SESSIONS_DIR, session['id'])
    captures_dir = os.path.join(session_dir, 'captures')
    detector.set_session(session['id'], captures_dir)
    
    return jsonify(session)

@app.route('/api/session/stop', methods=['POST'])
def stop_session_route():
    result = db.stop_session()
    return jsonify(result)

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    return jsonify(db.get_all_sessions())

@app.route('/api/source', methods=['POST'])
def set_source():
    data = request.json
    source = data.get('source')
    if source:
        camera.set_source(source)
        return jsonify({"status": "source_updated", "source": source})
    return jsonify({"error": "No source provided"}), 400

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    global streaming_thread
    if streaming_thread is None or not streaming_thread.is_alive():
        stop_streaming.clear()
        streaming_thread = socketio.start_background_task(generate_frames)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    # Optional: Stop streaming if no clients? 
    # For now keep running or handle gracefully

if __name__ == '__main__':
    # Ensure DB exists
    Config.init_app(app)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
