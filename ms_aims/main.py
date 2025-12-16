# main.py
import cv2
import time
import base64
import threading
import numpy as np
import os
import glob
from nicegui import ui, app

# Import Core Modules
from src.ai_engine import AIEngine
from src.dimension import DimensionCalculator

# --- KONFIGURASI ---
VIDEO_DIR = "ms_aims/data/videos"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# --- STATUS GLOBAL & MODULES ---
SYSTEM_STATUS = 'IDLE'
latest_frame = None
is_running = True
current_dimensions = {'w': 0, 'h': 0}

# Input Source State - Only video files from directory
input_source_path = ""  # Will be set when user selects a video
source_changed = False  # Flag to trigger reconnection

# Initialize Modules
ai_engine = AIEngine()
ai_engine.load_model()
dim_calc = DimensionCalculator(calibration_factor=None)

# --- HELPER FUNCTIONS ---
def get_video_files():
    """Scan VIDEO_DIR for video files."""
    if not os.path.exists(VIDEO_DIR):
        os.makedirs(VIDEO_DIR, exist_ok=True)
    
    # List specific extensions
    extensions = ['*.mp4', '*.avi', '*.mkv', '*.mov']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(VIDEO_DIR, ext)))
    
    # Return relative paths or full paths? Relative is cleaner for UI
    # But we need full path for cv2.VideoCapture
    return sorted(files)

# --- 1. CAMERA HANDLER (Background Thread) ---
def camera_loop():
    global latest_frame, is_running, current_dimensions, SYSTEM_STATUS, source_changed, input_source_path
    
    cap = None
    current_source = input_source_path
    
    print("Starting Video Player Loop")

    while is_running:
        # Reconnect logic if source changed or cap is None
        if cap is None or source_changed:
            if cap:
                cap.release()
            
            current_source = input_source_path
            
            # Validation: If no video file selected, don't try to open
            if not current_source or not os.path.exists(current_source):
                print("No valid video file selected. Waiting...")
                time.sleep(1)
                source_changed = False # Reset to avoid loop
                continue

            print(f"Opening Video File: {current_source}")
            cap = cv2.VideoCapture(current_source)
            source_changed = False
            
            if not cap.isOpened():
                print("Failed to open video file. Retrying in 2s...")
                time.sleep(2)
                continue

        ret, frame = cap.read()
        
        # Handle Video Loop (End of file)
        if not ret and cap.isOpened():
             print("Video ended, looping...")
             cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
             continue
        
        if ret:
            # --- AI PROCESSING PHASE 2 ---
            contour = ai_engine.run_segmentation(frame)
            
            if contour is not None:
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                w_mm, h_mm, box_points = dim_calc.measure_contour(contour)
                current_dimensions['w'] = w_mm
                current_dimensions['h'] = h_mm
                
                cv2.drawContours(frame, [box_points], 0, (0, 0, 255), 2)
                
                label = f"{w_mm:.1f} x {h_mm:.1f} mm"
                cv2.putText(frame, label, (box_points[0][0], box_points[0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                SYSTEM_STATUS = "DETECTED"
            else:
                SYSTEM_STATUS = "IDLE"

            # Encode for UI
            _, buffer = cv2.imencode('.jpg', frame)
            b64_image = base64.b64encode(buffer).decode('utf-8')
            latest_frame = f'data:image/jpeg;base64,{b64_image}'
            
            # FPS Control for video playback
            time.sleep(0.033)

    if cap:
        cap.release()
    print("Video player released.")

# --- 2. UI LOGIC (NiceGUI) ---
@ui.page('/')
def index():
    # Style Header
    with ui.header().classes('bg-blue-900 text-white items-center'):
        ui.label('MS-AIMS | Metal Sheet Inspector').classes('text-h6 font-bold')
        ui.space()
        status_label = ui.label('SYSTEM READY').classes('text-sm font-mono bg-green-600 px-2 rounded')

    # Main Content
    with ui.row().classes('w-full q-pa-md'):
        
        # LEFT: Video Feed & Source Control
        with ui.card().classes('w-2/3 h-full'):
            
            # --- INPUT SOURCE CONTROL ---
            with ui.row().classes('w-full items-center gap-4 mb-2'):
                ui.label('Video Source:').classes('font-bold')
            
            # Get available video files
            available_videos = get_video_files()
            
            # Video selection dropdown
            with ui.row().classes('w-full mb-2'):
                if available_videos:
                    # Create a display-friendly version for the dropdown
                    display_videos = [os.path.basename(video) for video in available_videos]
                    
                    ui.select(
                        options=display_videos, 
                        label='Select Video File', 
                        value=display_videos[0] if display_videos else None,
                        on_change=lambda e: select_video(e.value)
                    ).classes('w-full').props('outlined dense')
                    
                    # Auto-select the first video if available
                    if available_videos:
                        input_source_path = available_videos[0]
                        source_changed = True
                else:
                    ui.label('No video files found in ms_aims/data/videos').classes('text-red-500 w-full')
            
            # Video Container (id="c16")
            video_image = ui.interactive_image().classes('w-full rounded bg-black').props('id="c16"')
            
            # Create a placeholder for video mode
            video_placeholder = ui.row().classes('w-full h-64 bg-gray-200 rounded items-center justify-center hidden')
            with video_placeholder:
                ui.icon('movie', size='3xl').classes('text-gray-400')
                ui.label('No video selected').classes('text-gray-500 mt-2')
            
            # Function to handle video selection
            def select_video(selected_file_display):
                global input_source_path, source_changed, latest_frame
                
                # Find the full path from display name
                for video_path in available_videos:
                    if os.path.basename(video_path) == selected_file_display:
                        input_source_path = video_path
                        source_changed = True
                        # Clear the latest frame when switching video
                        latest_frame = None
                        ui.notify(f"Video selected: {selected_file_display}", type='positive')
                        break
            
            # Update UI based on video selection
            def update_video_ui():
                if input_source_path and os.path.exists(input_source_path):
                    # Hide placeholder and show video image
                    video_placeholder.classes('hidden')
                    video_image.classes('w-full rounded bg-black')
                else:
                    # Show placeholder when no video is selected
                    video_placeholder.classes('w-full h-64 bg-gray-200 rounded items-center justify-center flex flex-col')
                    video_image.classes('hidden')
            
            # Initial UI update
            update_video_ui()
        
        # RIGHT: Control Panel
        with ui.card().classes('w-1/3 h-full'):
            ui.label('Control Panel').classes('text-lg font-bold mb-4')
            
            # Dimensions Display
            with ui.grid(columns=2):
                ui.label('Length:')
                dim_l = ui.label('0.0 mm').classes('font-mono font-bold text-xl')
                ui.label('Width:')
                dim_w = ui.label('0.0 mm').classes('font-mono font-bold text-xl')

            ui.separator().classes('my-4')
            
            # Calibration Section
            ui.label('Calibration').classes('font-bold')
            cal_input = ui.number(label='Known Length (mm)', value=100).classes('w-full')
            
            def calibrate_now():
                if dim_calc.calibration_factor is None:
                     pixel_val = current_dimensions['w']
                else:
                     pixel_val = current_dimensions['w'] * dim_calc.calibration_factor
                
                if pixel_val > 0:
                     factor = dim_calc.set_calibration(pixel_val, cal_input.value)
                     ui.notify(f'Calibrated! Factor: {factor:.2f} px/mm', type='positive')
                else:
                     ui.notify('No object detected to calibrate!', type='warning')

            ui.button('CALIBRATE (Using Width)', on_click=calibrate_now).classes('w-full bg-orange-600 text-white')

            ui.separator().classes('my-4')
            log_area = ui.log().classes('w-full h-40 bg-gray-100 rounded p-2 text-xs')

    # --- 3. UI UPDATE LOOP ---
    async def update_state():
        if latest_frame:
            # Update video image with the latest frame
            video_image.set_source(latest_frame)
        
        dim_l.set_text(f"{current_dimensions['w']:.1f} mm")
        dim_w.set_text(f"{current_dimensions['h']:.1f} mm")
        
        status_label.set_text(SYSTEM_STATUS)
        if SYSTEM_STATUS == 'DETECTED':
            status_label.classes(replace='bg-blue-600')
        elif SYSTEM_STATUS == 'IDLE':
             status_label.classes(replace='bg-gray-600')

    ui.timer(0.1, update_state)

# --- LIFECYCLE ---
def startup():
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()

def shutdown():
    global is_running
    is_running = False

app.on_startup(startup)
app.on_shutdown(shutdown)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='MS-AIMS', port=8080, reload=False, native=False, storage_secret='ms-aims-secret-key')
