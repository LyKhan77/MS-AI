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

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Cores
db = Database()
camera = Camera()
detector = MetalSheetCounter()

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
            
            # Update session count in database only when it changes
            if not hasattr(generate_frames, '_last_count') or generate_frames._last_count != count:
                db.update_session_count(active_session['id'], count)
                generate_frames._last_count = count
        else:
            # No detection, just raw frame
            final_frame = frame
            count = 0
            # Reset last count when no session
            if hasattr(generate_frames, '_last_count'):
                delattr(generate_frames, '_last_count')
        
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
    confidence = data.get('confidence', 0.25)  # Get confidence from request
    
    # Check if stream is running
    if camera.source is None:
        return jsonify({"error": "No video source set. Please connect RTSP or upload video first."}), 400
    
    session = db.create_session(name, max_count)
    
    # Configure Detector for this session with confidence
    session_dir = os.path.join(Config.SESSIONS_DIR, session['id'])
    captures_dir = os.path.join(session_dir, 'captures')
    detector.set_session(session['id'], captures_dir, confidence)  # Pass confidence
    
    print(f"Session started: {session['id']}, confidence: {confidence}")
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
    """Get all sessions (simple list)"""
    return jsonify(db.get_all_sessions())

@app.route('/api/sessions/list', methods=['GET'])
def get_sessions_list():
    """Get paginated sessions list"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort', 'start_time')
    order = request.args.get('order', 'desc')
    
    result = db.get_sessions_paginated(page, per_page, sort_by, order)
    return jsonify(result)

@app.route('/api/sessions/<session_id>/captures', methods=['GET'])
def get_session_captures_route(session_id):
    """Get capture images for a session"""
    captures = db.get_session_captures(session_id)
    return jsonify({'session_id': session_id, 'captures': captures, 'count': len(captures)})

@app.route('/api/sessions/<session_id>/captures/<filename>', methods=['GET'])
def serve_capture_image(session_id, filename):
    """Serve capture image file"""
    from flask import send_from_directory
    captures_dir = os.path.join(Config.SESSIONS_DIR, session_id, 'captures')
    return send_from_directory(captures_dir, filename)

@app.route('/api/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get aggregate statistics"""
    stats = db.get_stats_overview()
    return jsonify(stats)

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session_route(session_id):
    """Delete a session and its data"""
    result = db.delete_session(session_id)
    return jsonify(result)

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


# ============================================================
# Defect Analysis Endpoints (SAM-3)
# ============================================================

@app.route('/api/sessions/<session_id>/analyze_defects', methods=['POST'])
def analyze_session_defects(session_id):
    """
    Run SAM-3 defect analysis on all captures from a session

    POST /api/sessions/<session_id>/analyze_defects
    Body (optional):
        {
            'defect_types': ['scratch', 'dent', 'rust', ...]
        }

    Response:
        {
            'status': 'completed' | 'error',
            'results': {...}
        }
    """
    from core.defect_analyzer import get_defect_analyzer

    # Get session
    session = db.get_session_by_id(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    # Get captures directory
    captures_dir = os.path.join(Config.SESSIONS_DIR, session_id, 'captures')
    if not os.path.exists(captures_dir):
        return jsonify({'error': 'No captures found'}), 404

    # Get defect types from request body
    data = request.get_json() or {}
    defect_types = data.get('defect_types')

    try:
        # Get analyzer instance
        analyzer = get_defect_analyzer()

        # Run analysis
        print(f"[API] Starting defect analysis for session {session_id}...")
        print(f"[API] Defect types: {defect_types if defect_types else 'All'}")
        results = analyzer.analyze_session_captures(session_id, captures_dir, defect_types)

        # Save results to database
        db.save_defect_analysis(session_id, results)

        print(f"[API] Analysis complete! Found {results['defects_found']} defects")

        return jsonify({
            'status': 'completed',
            'results': results
        }), 200

    except Exception as e:
        print(f"[API] Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/sessions/<session_id>/defects', methods=['GET'])
def get_session_defects(session_id):
    """
    Get all defects found in a session
    
    GET /api/sessions/<session_id>/defects
    
    Response:
        {
            'defects': [...],
            'stats_by_type': {...},
            'stats_by_severity': {...}
        }
    """
    defects = db.get_session_defects(session_id)
    stats_by_type = db.get_defect_stats_by_type(session_id)
    stats_by_severity = db.get_defect_stats_by_severity(session_id)
    
    return jsonify({
        'defects': defects,
        'stats_by_type': stats_by_type,
        'stats_by_severity': stats_by_severity
    }), 200


@app.route('/api/sessions/<session_id>/defects/export', methods=['GET'])
def export_session_defects(session_id):
    """
    Export all defect crops as ZIP file
    
    GET /api/sessions/<session_id>/defects/export
    
    Returns:
        ZIP file download
    """
    from flask import send_file
    import zipfile
    from io import BytesIO
    
    defects_dir = os.path.join(Config.SESSIONS_DIR, session_id, 'defects')
    
    if not os.path.exists(defects_dir):
        return jsonify({'error': 'No defects found'}), 404
    
    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(defects_dir):
            file_path = os.path.join(defects_dir, filename)
            if os.path.isfile(file_path):
                zip_file.write(file_path, filename)
    
    zip_buffer.seek(0)
    
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'session_{session_id}_defects.zip'
    )


@app.route('/api/sessions/<session_id>/defects/<filename>', methods=['GET'])
def get_defect_crop(session_id, filename):
    """
    Serve defect crop image
    
    GET /api/sessions/<session_id>/defects/<filename>
    """
    from flask import send_from_directory
    
    defects_dir = os.path.join(Config.SESSIONS_DIR, session_id, 'defects')
    return send_from_directory(defects_dir, filename)


@app.route('/api/sessions/<session_id>/defects/segmented/<filename>', methods=['GET'])
def get_segmented_image(session_id, filename):
    """
    Serve segmented image with overlays

    GET /api/sessions/<session_id>/defects/segmented/<filename>
    """
    from flask import send_from_directory
    from core.defect_analyzer import get_defect_analyzer

    segmented_dir = os.path.join(Config.SESSIONS_DIR, session_id, 'segmented')
    segmented_filename = f"segmented_{filename}"

    # Check if segmented image exists
    if not os.path.exists(os.path.join(segmented_dir, segmented_filename)):
        # Generate on-demand if not exists
        defects = db.get_defects_by_image(session_id, filename)
        if defects:
            analyzer = get_defect_analyzer()
            analyzer.generate_segmented_for_image(session_id, filename, defects)

    return send_from_directory(segmented_dir, segmented_filename)


# ============================================================
# Socket.IO Handlers
# ============================================================


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
