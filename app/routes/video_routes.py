"""
Video streaming routes
Provides MJPEG stream for real-time video display
"""

from flask import Blueprint, Response, current_app
import cv2

bp = Blueprint('video', __name__)

# Global session manager (will be set by app initialization)
session_manager = None


def set_session_manager(sm):
    """Set session manager instance"""
    global session_manager
    session_manager = sm


def generate_frames():
    """
    Generator function for MJPEG streaming
    
    Yields frames in multipart/x-mixed-replace format
    """
    if session_manager is None:
        # Return empty frame if no session manager
        yield b''
        return
    
    camera = session_manager.camera
    
    while True:
        # Get frame from camera
        frame = camera.get_frame()
        
        if frame is None:
            # No frame available, yield empty
            continue
        
        # Process frame for counting (if session active)
        if session_manager.is_processing and session_manager.active_session:
            frame = session_manager.process_frame_for_counting(frame)
        else:
            # Just show camera feed without processing
            # Add "No Active Session" overlay
            h, w = frame.shape[:2]
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 60), (10, 14, 26), -1)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            cv2.putText(
                frame,
                "No Active Session - Waiting...",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (156, 163, 175),  # Gray text
                2
            )
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, current_app.config.get('MJPEG_QUALITY', 85)])
        
        if not ret:
            continue
        
        # Convert to bytes
        frame_bytes = buffer.tobytes()
        
        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@bp.route('/video_feed')
def video_feed():
    """
    Video streaming route
    Returns MJPEG stream
    
    Usage in HTML:
    <img src="{{ url_for('video.video_feed') }}" />
    """
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
