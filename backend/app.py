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
    # Only start camera if source is set
    if camera.source is None:
        print("No camera source set. Waiting for source configuration...")
        while camera.source is None and not stop_streaming.is_set():
            socketio.sleep(1)
        if stop_streaming.is_set():
            return
    
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

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # Save to backend/data/videos/
    videos_dir = os.path.join(Config.DATA_DIR, 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    
    filepath = os.path.join(videos_dir, file.filename)
    file.save(filepath)
    
    # Auto-set as source
    camera.set_source(filepath)
    
    return jsonify({"status": "uploaded", "path": filepath})

@app.route('/api/source', methods=['POST'])
def set_source():
    data = request.json
    source = data.get('source')
    if source:
        camera.set_source(source)
        return jsonify({"status": "source_updated", "source": source})
    return jsonify({"error": "No source provided"}), 400

@app.route('/api/playback/pause', methods=['POST'])
def pause_playback():
    camera.pause()
    return jsonify({"status": "paused"})

@app.route('/api/playback/resume', methods=['POST'])
def resume_playback():
    camera.resume()
    return jsonify({"status": "resumed"})

@app.route('/api/playback/seek', methods=['POST'])
def seek_playback():
    data = request.json
    frame = data.get('frame', 0)
    camera.seek(int(frame))
    return jsonify({"status": "seeked", "frame": frame})

@app.route('/api/playback/info', methods=['GET'])
def playback_info():
    return jsonify(camera.get_playback_info())

@socketio.on('connect')
def handle_connect(auth=None):
    print('Client connected')
    global streaming_thread
    if streaming_thread is None:
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
