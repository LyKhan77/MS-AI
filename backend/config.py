import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_secret'
    
    # Paths
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    SESSIONS_DIR = os.path.join(DATA_DIR, 'sessions')
    DB_PATH = os.path.join(DATA_DIR, 'db.json')
    
    # Camera / RTSP
    # RTSP_URL = "rtsp://admin:password@192.168.1.100:554/stream" # Example
    RTSP_URL = 0 # Default to webcam 0 for dev
    FRAME_RATE = 30
    
    # Model Settings
    YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'yolo11m_metalsheet.pt')  # Trained YOLOv11m
    SAM_CHECKPOINT = "sam3_vit_h.pth" # Placeholder path
    
    # Analysis
    PIXEL_TO_MM_DEFAULT = 0.5 # Default calibration (override per session)

    # Defect Colors (BGR format for cv2)
    DEFECT_COLORS = {
        'scratch': [0, 0, 255],        # Red
        'dent': [0, 255, 0],           # Green
        'rust': [0, 165, 255],         # Orange
        'hole': [0, 255, 255],         # Yellow
        'coating_bubble': [255, 0, 255], # Magenta
        'oil_stain': [255, 0, 0],      # Blue
        'discoloration': [128, 128, 128], # Gray
        'pitting': [203, 192, 255],    # Pink
        'edge_burr': [42, 42, 165],    # Brown
        'warping': [255, 255, 0]       # Cyan
    }

    # Cors
    CORS_HEADERS = 'Content-Type'

    @staticmethod
    def init_app(app):
        os.makedirs(Config.SESSIONS_DIR, exist_ok=True)
