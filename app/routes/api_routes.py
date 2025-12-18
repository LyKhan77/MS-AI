"""
API routes for JSON endpoints
Handles session management, camera control, and status queries
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import os
from werkzeug.utils import secure_filename

bp = Blueprint('api', __name__)

# Global session manager (will be set by app initialization)
session_manager = None


def set_session_manager(sm):
    """Set session manager instance"""
    global session_manager
    session_manager = sm


# ============================================
# Session Management Endpoints
# ============================================

@bp.route('/session/start', methods=['POST'])
def start_session():
    """
    Start a new counting session
    
    Request JSON:
    {
        "session_name": "Batch A001",
        "max_count_target": 50
    }
    """
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    data = request.get_json()
    
    session_name = data.get('session_name')
    max_count_target = data.get('max_count_target')
    
    if not session_name or not max_count_target:
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        max_count_target = int(max_count_target)
    except ValueError:
        return jsonify({'error': 'max_count_target must be a number'}), 400
    
    try:
        session_data = session_manager.start_session(session_name, max_count_target)
        
        return jsonify({
            'status': 'success',
            'message': 'Session started',
            'session': session_data
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to start session: {str(e)}'}), 500


@bp.route('/session/finish', methods=['POST'])
def finish_session():
    """
    Finish current session
    
    Returns alert information if count doesn't match target
    """
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    try:
        summary = session_manager.finish_session()
        
        return jsonify({
            'status': 'success',
            'message': 'Session finished',
            'summary': summary
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to finish session: {str(e)}'}), 500


@bp.route('/session/status', methods=['GET'])
def session_status():
    """
    Get current session status
    
    Response:
    {
        "active": true,
        "session_id": "Batch_A001",
        "current_count": 23,
        "max_count_target": 50,
        "start_time": "2025-12-18T10:00:00",
        "state": "EMPTY_STABLE"
    }
    """
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    status = session_manager.get_session_status()
    
    if status is None:
        return jsonify({
            'active': False,
            'session_id': None,
            'current_count': 0,
            'max_count_target': 0,
            'start_time': None,
            'state': None
        })
    
    return jsonify(status)


# ============================================
# Camera Control Endpoints
# ============================================

@bp.route('/camera/set_rtsp', methods=['POST'])
def set_rtsp_url():
    """
    Update RTSP camera URL
    
    Request JSON:
    {
        "rtsp_url": "rtsp://..."
    }
    """
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    data = request.get_json()
    rtsp_url = data.get('rtsp_url')
    
    if not rtsp_url:
        return jsonify({'error': 'Missing rtsp_url'}), 400
    
    try:
        # Stop current camera and switch to new RTSP
        success = session_manager.camera.set_rtsp_url(rtsp_url)
        
        if not success:
            return jsonify({'error': 'Failed to connect to RTSP URL'}), 400
        
        return jsonify({
            'status': 'success',
            'message': 'RTSP URL updated',
            'rtsp_url': rtsp_url
        })
    except Exception as e:
        return jsonify({'error': f'Failed to set RTSP URL: {str(e)}'}), 500


@bp.route('/camera/upload_video', methods=['POST'])
def upload_video():
    """
    Upload video file for testing/simulation
    """
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Check file extension
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv'}
    filename = secure_filename(video_file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext not in allowed_extensions:
        return jsonify({'error': f'Invalid file type. Allowed: {allowed_extensions}'}), 400
    
    try:
        # Save uploaded file
        upload_dir = current_app.config.get('STATIC_DIR') / 'uploads'
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = upload_dir / filename
        video_file.save(str(filepath))
        
        # Switch camera to video file
        success = session_manager.camera.set_video_file(str(filepath))
        
        if not success:
            return jsonify({'error': 'Failed to open video file'}), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Video uploaded and loaded',
            'filename': filename,
            'filepath': str(filepath)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to upload video: {str(e)}'}), 500


# ============================================
# System Status Endpoints
# ============================================

@bp.route('/system/health', methods=['GET'])
def system_health():
    """
    Get system health status
    """
    if session_manager is None:
        return jsonify({
            'status': 'error',
            'message': 'System not initialized'
        }), 500
    
    # Get stats from all components
    camera_stats = session_manager.camera.get_stats()
    ai_stats = session_manager.ai.get_stats()
    counting_stats = session_manager.counting.get_stats()
    
    return jsonify({
        'status': 'healthy',
        'camera': {
            'connected': camera_stats['is_opened'],
            'fps': camera_stats['fps'],
            'resolution': f"{camera_stats['width']}x{camera_stats['height']}",
            'source_type': camera_stats['source_type']
        },
        'ai': {
            'model_loaded': ai_stats['is_loaded'],
            'device': ai_stats['device'],
            'cuda_available': ai_stats['cuda_available'],
            'avg_inference_time_ms': ai_stats['avg_inference_time_ms']
        },
        'counting': {
            'state': counting_stats['current_state'],
            'total_counts': counting_stats['total_counts'],
            'accuracy': counting_stats['accuracy']
        }
    })


@bp.route('/sessions/list', methods=['GET'])
def list_sessions():
    """Get list of all sessions"""
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    sessions = session_manager.storage.list_all_sessions()
    
    return jsonify({
        'sessions': sessions,
        'total': len(sessions)
    })


@bp.route('/sessions/<session_id>/details', methods=['GET'])
def get_session_details(session_id):
    """Get detailed session information"""
    if session_manager is None:
        return jsonify({'error': 'System not initialized'}), 500
    
    metadata = session_manager.storage.load_session_metadata(session_id)
    
    if not metadata:
        return jsonify({'error': 'Session not found'}), 404
    
    logs = session_manager.storage.load_detection_logs(session_id)
    images = session_manager.storage.get_session_images(session_id)
    
    return jsonify({
        'metadata': metadata,
        'detections': logs,
        'images': images,
        'total_captures': len(logs.get('captures', []))
    })
