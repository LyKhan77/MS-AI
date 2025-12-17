"""
Main Streamlit application for Metal Sheet AI Inspection System
Real-time metal sheet detection and counting using SAM-3
"""

import streamlit as st
import cv2
import numpy as np
import time
import threading
import logging
import sys
import os
from typing import Optional, Dict
import tempfile

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from camera import VideoStreamer, MotionDetector, InputSource
from detector import SAM3Engine
from processing import ImageProcessor
from ui_components import (
    render_sidebar_config,
    render_video_display,
    render_results_cards,
    render_detailed_results,
    render_calibration_tool,
    render_system_info,
    render_status_bar,
    create_overlay_image
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration with Jetson optimizations
st.set_page_config(
    page_title="Metal Sheet AI Inspection System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Jetson performance optimizations
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'

# Enable display for Jetson
try:
    os.environ['DISPLAY'] = ':0'
except:
    pass

# Session state initialization
def init_session_state():
    """Initialize session state variables"""
    # Initialize all required session state variables
    required_states = {
        'streamer': None,
        'detector': None, 
        'processor': None,
        'motion_detector': None,
        'is_running': False,
        'current_frame': None,
        'last_results': None,
        'processing_thread': None,
        'temp_video_path': None
    }
    
    for key, default_value in required_states.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def load_models():
    """Load AI models"""
    try:
        with st.spinner("Loading SAM-3 model..."):
            st.session_state.detector = SAM3Engine(
                model_name="facebook/sam3",
                confidence_threshold=0.5
            )
            
            if not st.session_state.detector.load_model():
                st.error("Failed to load SAM-3 model")
                return False
            
            st.session_state.processor = ImageProcessor(
                pixel_to_mm_ratio=1.0,
                sensitivity=0.1
            )
            
            st.session_state.motion_detector = MotionDetector(
                threshold=0.05,
                history_size=5
            )
            
        logger.info("Models loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        st.error(f"Error loading models: {e}")
        return False

def processing_loop():
    """Main processing loop running in separate thread"""
    logger.info("Processing loop started")
    
    try:
        while st.session_state.is_running:
            try:
                # Get frame from streamer
                frame = st.session_state.streamer.get_latest_frame()
                
                if frame is not None:
                    st.session_state.current_frame = frame.copy()
                    
                    # Check for motion/stability
                    is_stable = st.session_state.motion_detector.update(frame)
                    
                    if is_stable and st.session_state.detector:
                        # Process frame with SAM-3
                        detection_result = st.session_state.detector.detect_sheets(
                            frame,
                            text_prompt="metal sheet",
                            use_cache=True
                        )
                        
                        if detection_result:
                            # Calculate dimensions
                            pixel_to_mm = st.session_state.processor.dimension_calculator.pixel_to_mm_ratio
                            detection_result = st.session_state.detector.calculate_dimensions(
                                detection_result, pixel_to_mm
                            )
                            
                            # Detect defects
                            detection_result = st.session_state.detector.detect_defects(
                                detection_result, frame, 0.1
                            )
                            
                            # Convert to dict for session state
                            st.session_state.last_results = {
                                "count": detection_result.count,
                                "masks": detection_result.masks,
                                "boxes": detection_result.boxes,
                                "scores": detection_result.scores,
                                "processing_time": detection_result.processing_time,
                                "dimensions": detection_result.dimensions,
                                "quality_status": detection_result.quality_status
                            }
                    
                    # Small delay to prevent excessive CPU usage
                    time.sleep(0.01)
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)
                
    except Exception as e:
        logger.error(f"Critical error in processing loop: {e}")
    finally:
        logger.info("Processing loop stopped")

def start_monitoring(config: Dict):
    """Start video monitoring"""
    try:
        # Initialize models if not loaded
        if st.session_state.detector is None:
            if not load_models():
                return False
        
        # Update configuration
        if "pixel_to_mm" in config:
            st.session_state.processor.update_calibration(1.0, config["pixel_to_mm"])
        
        # Setup video source
        source_type = config.get("source_type", "Live Camera (RTSP/USB)")
        
        if source_type == "Live Camera (RTSP/USB)":
            rtsp_url = config.get("rtsp_url", "0")
            
            # Parse camera ID or RTSP URL
            if rtsp_url.isdigit():
                source = int(rtsp_url)
                input_type = InputSource.USB
            else:
                source = rtsp_url
                input_type = InputSource.RTSP
            
        else:  # Video File
            uploaded_file = config.get("uploaded_file")
            if uploaded_file is None:
                st.error("Please upload a video file")
                return False
            
            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                tmp_file.write(uploaded_file.read())
                st.session_state.temp_video_path = tmp_file.name
            
            source = st.session_state.temp_video_path
            input_type = InputSource.FILE
        
        # Create and configure streamer
        st.session_state.streamer = VideoStreamer(buffer_size=5)
        
        if not st.session_state.streamer.connect(source, input_type):
            st.error("Failed to connect to video source")
            return False
        
        if not st.session_state.streamer.start():
            st.error("Failed to start video streaming")
            return False
        
        # Start processing thread
        st.session_state.is_running = True
        st.session_state.processing_thread = threading.Thread(target=processing_loop, daemon=True)
        st.session_state.processing_thread.start()
        
        logger.info("Monitoring started successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        st.error(f"Error starting monitoring: {e}")
        return False

def stop_monitoring():
    """Stop video monitoring"""
    try:
        st.session_state.is_running = False
        
        # Stop streamer
        if st.session_state.streamer:
            st.session_state.streamer.stop()
            st.session_state.streamer = None
        
        # Wait for processing thread to finish
        if st.session_state.processing_thread and st.session_state.processing_thread.is_alive():
            st.session_state.processing_thread.join(timeout=2.0)
        
        # Clean up temp file
        if st.session_state.temp_video_path and os.path.exists(st.session_state.temp_video_path):
            os.unlink(st.session_state.temp_video_path)
            st.session_state.temp_video_path = None
        
        # Clear current frame
        st.session_state.current_frame = None
        
        logger.info("Monitoring stopped")
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")

def main():
    """Main application function"""
    # Initialize session state
    init_session_state()
    
    # Render header
    st.markdown("""
    # 🔧 Metal Sheet AI Inspection System
    **Real-time metal sheet detection and quality control using SAM-3**
    """)
    
    # Render sidebar configuration
    config = render_sidebar_config()
    
    # Handle start/stop buttons
    if config["start_button"] and not st.session_state.is_running:
        if start_monitoring(config):
            st.success("Monitoring started successfully!")
    
    if config["stop_button"] and st.session_state.is_running:
        stop_monitoring()
        st.success("Monitoring stopped!")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Video display
        frame = st.session_state.current_frame
        
        # Create overlay with detection results
        if frame is not None and st.session_state.last_results:
            frame_with_overlay = create_overlay_image(
                frame, 
                st.session_state.last_results,
                config.get("pixel_to_mm", 1.0)
            )
        else:
            frame_with_overlay = frame
        
        render_video_display(
            frame_with_overlay,
            st.session_state.streamer.get_info()["fps"] if st.session_state.streamer else 0.0
        )
    
    with col2:
        # Results cards
        render_results_cards(st.session_state.last_results)
        
        # System info
        if st.session_state.detector:
            system_info = st.session_state.detector.get_model_info()
            render_system_info(system_info)
    
    # Detailed results section
    if st.session_state.last_results:
        render_detailed_results(st.session_state.last_results)
    
    # Calibration tool
    calibration_result = render_calibration_tool()
    if calibration_result:
        pixel_length, real_length = calibration_result
        if st.session_state.processor:
            st.session_state.processor.update_calibration(pixel_length, real_length)
    
    # Status bar
    if st.session_state.is_running:
        render_status_bar("processing", "Analyzing metal sheets...")
    elif st.session_state.last_results:
        render_status_bar("success", "Detection complete")
    else:
        render_status_bar("idle", "Ready to start monitoring")
    
    # Cleanup on page unload
    def cleanup():
        if st.session_state.is_running:
            stop_monitoring()
    
    # Register cleanup
    import atexit
    atexit.register(cleanup)

if __name__ == "__main__":
    main()
