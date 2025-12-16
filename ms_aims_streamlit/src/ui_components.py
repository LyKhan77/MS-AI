"""
Reusable Streamlit UI components for the metal sheet detection system
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import time
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


def render_sidebar_config() -> Dict:
    """Render sidebar configuration panel"""
    with st.sidebar:
        st.markdown("### 🔧 Configuration")
        
        # Input source selection
        st.markdown("#### Input Source")
        source_type = st.radio(
            "Select Input Source:",
            ["Live Camera (RTSP/USB)", "Video File (Upload)"],
            key="source_type"
        )
        
        config = {"source_type": source_type}
        
        if source_type == "Live Camera (RTSP/USB)":
            rtsp_url = st.text_input(
                "RTSP URL / Camera ID:",
                value="0",
                help="Enter RTSP URL or camera index (e.g., 0 for default webcam)"
            )
            config["rtsp_url"] = rtsp_url
            
        else:
            uploaded_file = st.file_uploader(
                "Upload Video File:",
                type=["mp4", "avi", "mov"],
                help="Upload video file for analysis"
            )
            config["uploaded_file"] = uploaded_file
        
        st.markdown("---")
        
        # Calibration settings
        st.markdown("#### Calibration")
        pixel_to_mm = st.number_input(
            "Pixel to MM Ratio:",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Conversion ratio from pixels to millimeters"
        )
        config["pixel_to_mm"] = pixel_to_mm
        
        st.markdown("---")
        
        # Detection settings
        st.markdown("#### Detection Settings")
        confidence_threshold = st.slider(
            "Confidence Threshold:",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        config["confidence_threshold"] = confidence_threshold
        
        defect_sensitivity = st.slider(
            "Defect Sensitivity:",
            min_value=0.0,
            max_value=1.0,
            value=0.1,
            step=0.05,
            help="Higher values detect more defects"
        )
        config["defect_sensitivity"] = defect_sensitivity
        
        st.markdown("---")
        
        # Action buttons
        st.markdown("#### Actions")
        start_button = st.button(
            "▶️ START Monitoring",
            type="primary",
            key="start_button"
        )
        config["start_button"] = start_button
        
        stop_button = st.button(
            "⏹️ STOP",
            key="stop_button"
        )
        config["stop_button"] = stop_button
        
        save_ng_images = st.checkbox(
            "Save NG Images",
            value=True,
            help="Automatically save images with defects"
        )
        config["save_ng_images"] = save_ng_images
        
        return config


def render_video_display(frame: Optional[np.ndarray], fps: float = 0.0) -> None:
    """Render video display area"""
    st.markdown("### 📹 Live Video Feed")
    
    if frame is not None:
        # Convert BGR to RGB for Streamlit
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Display frame
        st.image(
            rgb_frame,
            channels="RGB",
            use_column_width=True,
            caption=f"FPS: {fps:.1f}"
        )
    else:
        # Placeholder when no frame available
        st.image(
            np.zeros((480, 640, 3), dtype=np.uint8),
            channels="RGB",
            use_column_width=True,
            caption="No video feed"
        )


def render_results_cards(detection_results: Optional[Dict]) -> None:
    """Render results cards showing detection statistics"""
    st.markdown("### 📊 Detection Results")
    
    # Create three columns for results
    col1, col2, col3 = st.columns(3)
    
    if detection_results is None:
        # Default/empty state
        with col1:
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: #666; margin: 0;">STATUS</h3>
                <p style="color: #999; font-size: 24px; margin: 10px 0;">Idle</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: #666; margin: 0;">COUNT</h3>
                <p style="color: #999; font-size: 24px; margin: 10px 0;">0</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: #666; margin: 0;">AVG LENGTH</h3>
                <p style="color: #999; font-size: 24px; margin: 10px 0;">-- mm</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Extract results
        count = detection_results.get("count", 0)
        dimensions = detection_results.get("dimensions", [])
        quality_status = detection_results.get("quality_status", [])
        processing_time = detection_results.get("processing_time", 0)
        
        # Calculate average dimensions
        avg_length = 0
        if dimensions:
            avg_length = np.mean([d.get("length", 0) for d in dimensions])
        
        # Determine overall status
        overall_status = "OK"
        if "NG" in quality_status:
            overall_status = "NG"
        status_color = "#28a745" if overall_status == "OK" else "#dc3545"
        
        with col1:
            st.markdown(f"""
            <div style="background-color: {status_color}; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: white; margin: 0;">STATUS</h3>
                <p style="color: white; font-size: 24px; margin: 10px 0;">{overall_status}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background-color: #007bff; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: white; margin: 0;">COUNT</h3>
                <p style="color: white; font-size: 24px; margin: 10px 0;">{count}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background-color: #6c757d; padding: 20px; border-radius: 10px; text-align: center;">
                <h3 style="color: white; margin: 0;">AVG LENGTH</h3>
                <p style="color: white; font-size: 24px; margin: 10px 0;">{avg_length:.1f} mm</p>
            </div>
            """, unsafe_allow_html=True)


def render_detailed_results(detection_results: Optional[Dict]) -> None:
    """Render detailed results with expandable sections"""
    if detection_results is None:
        return
    
    with st.expander("📋 Detailed Results", expanded=False):
        # Processing time
        st.markdown(f"**Processing Time:** {detection_results.get('processing_time', 0):.3f} seconds")
        
        # Dimensions table
        dimensions = detection_results.get("dimensions", [])
        quality_status = detection_results.get("quality_status", [])
        
        if dimensions:
            st.markdown("**Detected Sheets:**")
            
            # Create table data
            table_data = []
            for i, (dim, status) in enumerate(zip(dimensions, quality_status)):
                table_data.append({
                    "Sheet #": i + 1,
                    "Length (mm)": f"{dim.get('length', 0):.1f}",
                    "Width (mm)": f"{dim.get('width', 0):.1f}",
                    "Angle (°)": f"{dim.get('angle', 0):.1f}",
                    "Status": status
                })
            
            # Display as DataFrame
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
        
        # Quality analysis
        quality_analysis = detection_results.get("quality_analysis", {})
        if quality_analysis:
            st.markdown("**Quality Analysis:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Overall Quality", f"{quality_analysis.get('confidence', 0):.2%}")
                st.metric("Edge Density", f"{quality_analysis.get('edge_density', 0):.3f}")
            
            with col2:
                defects = quality_analysis.get('defects', [])
                if defects:
                    st.markdown("**Detected Defects:**")
                    for defect in defects:
                        st.markdown(f"- {defect.replace('_', ' ').title()}")
                else:
                    st.markdown("✅ No defects detected")


def render_calibration_tool() -> Optional[Tuple[float, float]]:
    """Render calibration tool for pixel-to-mm conversion"""
    with st.expander("📏 Calibration Tool", expanded=False):
        st.markdown("""
        Use this tool to calibrate the pixel-to-millimeter conversion ratio.
        Place an object of known size in the view and measure it.
        """)
        
        # Upload calibration image
        calib_image = st.file_uploader(
            "Upload calibration image:",
            type=["jpg", "jpeg", "png"],
            key="calib_image"
        )
        
        if calib_image is not None:
            # Display image
            image = Image.open(calib_image)
            st.image(image, caption="Click two points to measure distance")
            
            # Get known length
            known_length = st.number_input(
                "Known length (mm):",
                min_value=1.0,
                value=100.0,
                step=1.0
            )
            
            # Placeholder for pixel measurement
            st.markdown("**Click on the image to measure distance in pixels**")
            st.info("Note: Interactive pixel measurement feature requires additional implementation")
            
            if st.button("Calculate Ratio"):
                # Placeholder calculation
                pixel_length = st.number_input(
                    "Measured pixel length:",
                    min_value=1.0,
                    value=100.0,
                    step=1.0
                )
                
                if pixel_length > 0:
                    ratio = known_length / pixel_length
                    st.success(f"Pixel-to-MM ratio: {ratio:.4f}")
                    st.session_state["calibration_ratio"] = ratio
                    
                    return pixel_length, known_length
        
        return None


def render_system_info(system_info: Dict) -> None:
    """Render system information panel"""
    with st.expander("ℹ️ System Information", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Model:**")
            st.text(f"Name: {system_info.get('model_name', 'N/A')}")
            st.text(f"Device: {system_info.get('device', 'N/A')}")
            st.text(f"Loaded: {system_info.get('loaded', False)}")
        
        with col2:
            st.markdown("**Performance:**")
            st.text(f"Confidence Threshold: {system_info.get('confidence_threshold', 0.5)}")
            st.text(f"Vision Cache: {system_info.get('vision_cache_size', 0)} items")
            st.text(f"Text Cache: {system_info.get('text_cache_size', 0)} items")


def render_status_bar(status: str, message: str = "") -> None:
    """Render status bar at bottom of page"""
    status_colors = {
        "idle": "#6c757d",
        "processing": "#ffc107",
        "success": "#28a745",
        "error": "#dc3545"
    }
    
    color = status_colors.get(status.lower(), "#6c757d")
    
    st.markdown(f"""
    <div style="background-color: {color}; color: white; padding: 10px; border-radius: 5px; 
                margin-top: 20px; text-align: center;">
        <strong>Status:</strong> {status.upper()} {message}
    </div>
    """, unsafe_allow_html=True)


def create_overlay_image(original_frame: np.ndarray, 
                        detection_results: Optional[Dict],
                        pixel_to_mm_ratio: float = 1.0) -> np.ndarray:
    """Create overlay image with detection results"""
    if detection_results is None or original_frame is None:
        return original_frame
    
    overlay = original_frame.copy()
    
    # Get detection data
    masks = detection_results.get("masks", [])
    boxes = detection_results.get("boxes", [])
    dimensions = detection_results.get("dimensions", [])
    quality_status = detection_results.get("quality_status", [])
    
    # Draw detections
    for i in range(len(masks)):
        if i >= len(masks):
            break
            
        mask = masks[i]
        status = quality_status[i] if i < len(quality_status) else "UNKNOWN"
        
        # Choose color based on status
        color = (0, 255, 0) if status == "OK" else (0, 0, 255)
        
        # Draw mask overlay
        overlay[mask > 0] = overlay[mask > 0] * 0.7 + np.array(color) * 0.3
        
        # Draw bounding box
        if i < len(boxes):
            box = boxes[i].astype(int)
            cv2.rectangle(overlay, (box[0], box[1]), (box[2], box[3]), color, 2)
            
            # Add dimensions text
            if i < len(dimensions):
                dim = dimensions[i]
                label = f"L:{dim['length']:.1f}mm W:{dim['width']:.1f}mm"
                
                # Position text
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                text_x = box[0]
                text_y = box[1] - 10 if box[1] > 30 else box[1] + text_size[1] + 10
                
                # Draw text background
                cv2.rectangle(
                    overlay,
                    (text_x - 5, text_y - text_size[1] - 5),
                    (text_x + text_size[0] + 5, text_y + 5),
                    (255, 255, 255),
                    -1
                )
                
                # Draw text
                cv2.putText(
                    overlay,
                    label,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )
    
    return overlay
