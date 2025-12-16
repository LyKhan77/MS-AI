# main.py
import cv2
import time
import base64
import threading
import numpy as np
from nicegui import ui, app

# Import Core Modules
from src.ai_engine import AIEngine
from src.dimension import DimensionCalculator

# --- KONFIGURASI SEDERHANA ---
# CAMERA_ID = 0 
CAMERA_ID = "rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1"
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# --- STATUS GLOBAL & MODULES ---
SYSTEM_STATUS = 'IDLE'
latest_frame = None
is_running = True
current_dimensions = {'w': 0, 'h': 0}

# Initialize Modules
ai_engine = AIEngine()
ai_engine.load_model()
dim_calc = DimensionCalculator(calibration_factor=None) # Uncalibrated initially

# --- 1. CAMERA HANDLER (Background Thread) ---
def camera_loop():
    global latest_frame, is_running, current_dimensions, SYSTEM_STATUS
    
    # Retry logic for Camera
    cap = None
    while is_running and cap is None:
        try:
            print(f"Connecting to Camera: {CAMERA_ID}")
            cap = cv2.VideoCapture(CAMERA_ID)
            if not cap.isOpened():
                print("Failed to open camera. Retrying in 5s...")
                cap = None
                time.sleep(5)
        except Exception as e:
            print(f"Camera Error: {e}")
            time.sleep(5)

    # Main Loop
    while is_running:
        ret, frame = cap.read()
        if ret:
            # Resize for consistent processing speed if needed
            # frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            
            # --- AI PROCESSING PHASE 2 ---
            # 1. Segmentation
            contour = ai_engine.run_segmentation(frame)
            
            if contour is not None:
                # 2. Draw Contour
                cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                
                # 3. Calculate Dimensions
                w_mm, h_mm, box_points = dim_calc.measure_contour(contour)
                current_dimensions['w'] = w_mm
                current_dimensions['h'] = h_mm
                
                # Draw Bounding Box
                cv2.drawContours(frame, [box_points], 0, (0, 0, 255), 2)
                
                # Draw Text
                label = f"{w_mm:.1f} x {h_mm:.1f} mm"
                cv2.putText(frame, label, (box_points[0][0], box_points[0][1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                SYSTEM_STATUS = "DETECTED"
            else:
                SYSTEM_STATUS = "IDLE"

            # Encode to JPEG for Web UI
            _, buffer = cv2.imencode('.jpg', frame)
            b64_image = base64.b64encode(buffer).decode('utf-8')
            latest_frame = f'data:image/jpeg;base64,{b64_image}'
        else:
            print("Camera stream lost. Reconnecting...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_ID)
        
        # Limit FPS
        time.sleep(0.03) 

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
        
        # Video Feed
        with ui.card().classes('w-2/3 h-full'):
            ui.label('Live Monitoring').classes('text-lg font-bold mb-2')
            video_image = ui.interactive_image().classes('w-full rounded bg-black')
        
        # Control Panel
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
                # Simple logic: assume current detected width corresponds to known length
                # In real app, might want to specify which side
                if current_dimensions['w'] > 0:
                    # Use the width (longest side usually) as reference
                    # Or calculate hypotenuse if diagonal. 
                    # For now, let's just use the 'Width' read by the system.
                    # We need the pixel width, but our current_dimensions are already mm (if calibrated)
                    # or uncalibrated units if factor is 1.0.
                    
                    # To do this correctly, we need the raw pixel width from the engine.
                    # But for simplicity in Phase 2, let's assume dim_calc.pixels_to_mm 
                    # was returning raw pixels if factor was 1.0 (which it does if None).
                    
                    # Note: measure_contour returns 0.0 if not calibrated? 
                    # Let's fix dimension.py behavior to return pixels if factor is None.
                    pass 

                # Better approach: We need the pixel reading.
                # Since we don't have direct access to "current pixels" here easily without global,
                # let's cheat slightly and use the 'current_dimensions' assuming they are 
                # pixels if not yet calibrated.
                
                # Check if system is uncalibrated
                if dim_calc.calibration_factor is None:
                     # w_mm is actually w_pixels here
                     pixel_val = current_dimensions['w']
                else:
                     # Back-calculate pixels? Or just reset factor to None first?
                     # Let's simple reset for now if needed.
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
        # Update Image
        if latest_frame:
            video_image.set_source(latest_frame)
        
        # Update Labels
        dim_l.set_text(f"{current_dimensions['w']:.1f} mm")
        dim_w.set_text(f"{current_dimensions['h']:.1f} mm")
        
        # Update Status
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
