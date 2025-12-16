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
DEFAULT_RTSP = "rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1"
VIDEO_DIR = "ms_aims/data/videos"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# --- STATUS GLOBAL & MODULES ---
SYSTEM_STATUS = 'IDLE'
latest_frame = None
is_running = True
current_dimensions = {'w': 0, 'h': 0}

# Input Source State
input_source_type = 'STREAM' # 'STREAM' or 'VIDEO'
input_source_path = DEFAULT_RTSP
source_changed = False # Flag to trigger reconnection

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
    
    print(f"Starting Camera Loop with: {current_source}")

    while is_running:
        # Reconnect logic if source changed or cap is None
        if cap is None or source_changed:
            if cap:
                cap.release()
            
            current_source = input_source_path
            
            # Validation: If video mode but no file, don't try to open
            if input_source_type == 'VIDEO' and (not current_source or not os.path.exists(current_source)):
                print("No valid video file selected. Waiting...")
                time.sleep(1)
                source_changed = False # Reset to avoid loop
                continue

            print(f"Opening Source: {current_source}")
            cap = cv2.VideoCapture(current_source)
            source_changed = False
            
            if not cap.isOpened():
                print("Failed to open source. Retrying in 2s...")
                time.sleep(2)
                continue

        ret, frame = cap.read()
        
        # Handle Video Loop (End of file)
        if not ret and input_source_type == 'VIDEO' and cap.isOpened():
             print("Video ended, looping...")
             cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
             continue
        elif not ret and input_source_type == 'STREAM':
             print("Stream lost, reconnecting...")
             cap.release()
             cap = None
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
            
            # FPS Control
            if input_source_type == 'VIDEO':
                time.sleep(0.033)
            else:
                time.sleep(0.01)

    if cap:
        cap.release()
    print("Camera released.")

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
                ui.label('Input Source:').classes('font-bold')
            
            # Video Container (id="c16")
            video_image = ui.interactive_image().classes('w-full rounded bg-black').props('id="c16"')
            
            # Create a placeholder for video mode
            video_placeholder = ui.row().classes('w-full h-64 bg-gray-200 rounded items-center justify-center hidden')
            with video_placeholder:
                ui.icon('movie', size='3xl').classes('text-gray-400')
                ui.label('No video selected').classes('text-gray-500 mt-2')
            
            # Dynamic container based on selected input source
            input_container = ui.row().classes('w-full mt-2')
            
            # Define functions after UI elements are created
            def update_input_ui():
                input_container.clear()
                with input_container:
                    if input_source_type == 'STREAM':
                        # For STREAM mode, no input needed - just show a label
                        ui.label('Camera stream will be displayed below').classes('text-sm text-gray-600 w-full')
                        # Hide placeholder and show video image
                        video_placeholder.classes('hidden')
                        video_image.classes('w-full rounded bg-black')
                    else:
                        # For VIDEO mode, show file browser
                        with ui.row().classes('w-full'):
                            ui.upload(label='Select Video File', multiple=False, 
                                    on_upload=on_file_upload, 
                                    accept='.mp4,.avi,.mkv,.mov').classes('w-full')
                        
                        # Show current video file if any
                        if input_source_path:
                            file_display = os.path.basename(input_source_path)
                            ui.label(f'Selected: {file_display}').classes('text-sm text-blue-600 mt-1')
                            # Hide placeholder and show video image
                            video_placeholder.classes('hidden')
                            video_image.classes('w-full rounded bg-black')
                        else:
                            # Show placeholder when no video is selected
                            video_placeholder.classes('w-full h-64 bg-gray-200 rounded items-center justify-center flex flex-col')
                            video_image.classes('hidden')
            
            def on_source_change(e):
                global input_source_type, input_source_path, source_changed, latest_frame
                input_source_type = e.value
                
                # Set default path when switching
                if input_source_type == 'STREAM':
                    input_source_path = DEFAULT_RTSP
                else:
                    # For video mode, clear path until file is selected
                    input_source_path = ""
                    # Clear the latest frame when switching to video mode
                    latest_frame = None
                
                source_changed = True
                update_input_ui()  # Refresh UI
                ui.notify(f"Switched to {input_source_type}")

            def on_file_upload(e):
                global input_source_path, source_changed
                # Check file extension
                valid_extensions = ['.mp4', '.avi', '.mkv', '.mov']
                file_ext = os.path.splitext(e.name)[1].lower()
                
                if file_ext not in valid_extensions:
                    ui.notify("Please select a valid video file (.mp4, .avi, .mkv, .mov)", type='negative')
                    return
                
                # Save uploaded file to temporary location
                if e.content:
                    temp_dir = os.path.join(os.getcwd(), "ms_aims", "data", "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate a temporary file path
                    temp_file = os.path.join(temp_dir, e.name)
                    with open(temp_file, 'wb') as f:
                        f.write(e.content.read())
                    
                    input_source_path = temp_file
                    source_changed = True
                    update_input_ui()  # Refresh UI to show selected file
                    ui.notify(f"Video uploaded: {e.name}", type='positive')
                else:
                    ui.notify("Upload failed", type='warning')
            
            # Radio Button for Stream/Video selection
            with ui.row().classes('w-full'):
                ui.radio(['STREAM', 'VIDEO'], value=input_source_type, on_change=on_source_change).props('inline')
            
            # Initial Render
            update_input_ui()
        
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
            # Only update video image if it's visible (not hidden)
            if 'hidden' not in video_image.classes:
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
