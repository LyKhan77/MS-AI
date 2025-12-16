# main.py
import cv2
import time
import base64
import threading
import numpy as np
from nicegui import ui, app

# --- KONFIGURASI SEDERHANA (Nanti pindahkan ke yaml) ---
CAMERA_ID = 0  # Ganti ke '/dev/video0' atau string RTSP jika perlu
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# --- STATUS GLOBAL (Shared State) ---
# Di production nanti gunakan Manager/Queue dari multiprocessing
app.storage.user['status'] = 'IDLE'
latest_frame = None
is_running = True

# --- 1. CAMERA HANDLER (Running in Background Thread) ---
def camera_loop():
    global latest_frame, is_running
    cap = cv2.VideoCapture(CAMERA_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    
    print(f"Camera started on ID {CAMERA_ID}")

    while is_running:
        ret, frame = cap.read()
        if ret:
            # --- SIMULASI AI PROCESS DI SINI ---
            # Nanti logika SAM3 dan Deteksi dimasukkan di sini
            # Contoh sederhana: Gambar kotak merah jika status NG
            
            # Encode frame ke JPEG lalu ke Base64 untuk dikirim ke UI
            _, buffer = cv2.imencode('.jpg', frame)
            b64_image = base64.b64encode(buffer).decode('utf-8')
            latest_frame = f'data:image/jpeg;base64,{b64_image}'
        else:
            print("Failed to read camera.")
            time.sleep(1)
        
        # Limit FPS agar CPU tidak 100% (Sleep kecil)
        time.sleep(0.03) 

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

    # Main Content Split (Video & Controls)
    with ui.row().classes('w-full q-pa-md'):
        
        # KIRI: Video Feed
        with ui.card().classes('w-2/3 h-full'):
            ui.label('Live Monitoring').classes('text-lg font-bold mb-2')
            # Image container placeholder
            video_image = ui.interactive_image().classes('w-full rounded bg-black')
        
        # KANAN: Control & Stats
        with ui.card().classes('w-1/3 h-full'):
            ui.label('Control Panel').classes('text-lg font-bold mb-4')
            
            # Indikator Dimensi (Dummy)
            with ui.grid(columns=2):
                ui.label('Length:')
                dim_l = ui.label('0 mm').classes('font-mono font-bold')
                ui.label('Width:')
                dim_w = ui.label('0 mm').classes('font-mono font-bold')

            ui.separator().classes('my-4')
            
            # Log Panel
            log_area = ui.log().classes('w-full h-40 bg-gray-100 rounded p-2 text-xs')
            
            # Tombol Manual Trigger (Untuk Testing)
            def manual_trigger():
                log_area.push(f'{time.strftime("%H:%M:%S")} - Manual Trigger Activated')
                ui.notify('Processing...', type='info')
                # Simulasi hasil
                status_label.set_text('PROCESSING...')
                status_label.classes(replace='bg-yellow-600')
                
                # Simulasi delay AI
                ui.timer(1.0, lambda: finish_process(), once=True)

            def finish_process():
                # Random Result simulation
                import random
                is_defect = random.choice([True, False])
                
                if is_defect:
                    status_label.set_text('NG - DEFECT DETECTED')
                    status_label.classes(replace='bg-red-600')
                    ui.notify('REJECTED!', type='negative')
                    log_area.push('Result: NG (Scratched)')
                else:
                    status_label.set_text('OK - PASS')
                    status_label.classes(replace='bg-green-600')
                    ui.notify('PASSED', type='positive')
                    log_area.push('Result: OK')
                    dim_l.set_text(f'{random.randint(290,310)} mm')
                    dim_w.set_text(f'{random.randint(190,210)} mm')

            ui.button('TRIGGER CHECK', on_click=manual_trigger).classes('w-full bg-blue-700 text-white')

    # --- 3. UI UPDATE LOOP ---
    # Fungsi ini dipanggil browser setiap 100ms untuk update gambar
    async def update_video_feed():
        if latest_frame:
            video_image.set_source(latest_frame)

    ui.timer(0.1, update_video_feed) # 10 FPS update rate di UI

# --- LIFECYCLE MANAGEMENT ---
def startup():
    # Jalankan kamera di thread terpisah agar UI tidak freeze
    t = threading.Thread(target=camera_loop, daemon=True)
    t.start()

def shutdown():
    global is_running
    is_running = False

app.on_startup(startup)
app.on_shutdown(shutdown)

# Jalankan App
if __name__ in {"__main__", "__mp_main__"}:
    # native=False agar tidak error di Jetson (Headless)
    # port 8080 agar mudah diakses
    ui.run(title='MS-AIMS', port=8080, reload=False, native=False, storage_secret='ms-aims-secret-key')
