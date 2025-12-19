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
    Background thread function to capture frames, run detection only if session active
    """
    # Only start camera if source is set
    if camera.source is None:
        print("No camera source set. Waiting for source configuration...")
        while camera.source is None and not stop_streaming.is_set():
            socketio.sleep(1)
        if stop_streaming.is_set():
            return
    
    camera.start()
    consecutive_failures = 0
    max_failures = 10
    
    while not stop_streaming.is_set():
        ret, frame = camera.get_frame()
        
        if not ret:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                print("Too many frame failures, stopping stream")
                break
            socketio.sleep(0.1)
            continue
        
        consecutive_failures = 0

        # Check if session is active
        active_session = db.get_active_session()
        
        # Debug logging
        if active_session and not hasattr(generate_frames, '_session_logged'):
            print(f"[DEBUG] Session active: {active_session['id']}, is_paused: {camera.is_paused}")
            generate_frames._session_logged = True
        elif not active_session and hasattr(generate_frames, '_session_logged'):
            print("[DEBUG] No active session, raw stream mode")
            delattr(generate_frames, '_session_logged')
        
        if active_session:
            # Run detection only when session is active
            count, debug_frame = detector.process(frame)
            final_frame = debug_frame if debug_frame is not None else frame
        else:
            # No detection, just raw frame
            final_frame = frame
            count = 0
        
        # Prepare frame for streaming (JPEG -> Base64)
        _, buffer = cv2.imencode('.jpg', final_frame)
        frame_bytes = base64.b64encode(buffer).decode('utf-8')
        
        # Emit to client
        socketio.emit('video_frame', {
            'image': frame_bytes, 
            'count': count,
            'session_active': active_session is not None
        })
        
        socketio.sleep(1 / Config.FRAME_RATE) 
    
    camera.stop()
    print("Streaming thread exited cleanly")

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"status": "running"})

@app.route('/api/session/start', methods=['POST'])
def start_session():
    data = request.json
    name = data.get('name', 'Untitled')
    max_count = data.get('max_count', 100)
    
    # Check if stream is running
    if camera.source is None:
        return jsonify({"error": "No video source set. Please connect RTSP or upload video first."}), 400
    
    session = db.create_session(name, max_count)
    
    # Configure Detector for this session
    session_dir = os.path.join(Config.SESSIONS_DIR, session['id'])
    captures_dir = os.path.join(session_dir, 'captures')
    detector.set_session(session['id'], captures_dir)
    
    print(f"Session started: {session['id']}")
    return jsonify(session)

@app.route('/api/session/stop', methods=['POST'])
def stop_session_route():
    result = db.stop_session()
    
    # Reset detector
    detector.set_session(None, None)
    
    print("Session stopped")
    return jsonify(result)

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    return jsonify(db.get_all_sessions())

@app.route('/api/upload', methods=['POST'])
def upload_video():
    global streaming_thread
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    # Stop existing stream if running
    if streaming_thread:
        print("Stopping existing stream before upload...")
        stop_streaming.set()
        time.sleep(0.5)
        streaming_thread = None
    
    # Reset event for new stream
    stop_streaming.clear()
    
    # Save to backend/data/videos/
    videos_dir = os.path.join(Config.DATA_DIR, 'videos')
    os.makedirs(videos_dir, exist_ok=True)
    
    filepath = os.path.join(videos_dir, file.filename)
    file.save(filepath)
    
    # Auto-set as source (stream will start via SocketIO)
    camera.set_source(filepath)
    
    return jsonify({"status": "uploaded", "path": filepath})

@app.route('/api/source', methods=['POST'])
def set_source():
    data = request.json
    source = data.get('source')
    if source:
        camera.set_source(source)
        return jsonify({"status": "source updated", "source": source})
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

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    global streaming_thread
    
    print("Stopping camera and streaming thread...")
    
    # Signal thread to stop
    stop_streaming.set()
    
    # Stop camera
    camera.stop()
    
    # Wait for thread to finish
    if streaming_thread:
        time.sleep(0.5)  # Give thread time to exit
        streaming_thread = None
    
    # Clear source
    camera.source = None
    
    print("Camera stopped successfully")
    return jsonify({"status": "stopped"})

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
