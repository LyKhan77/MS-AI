"""
Configuration settings for Metal Sheet QC Detection System
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Flask Configuration
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Paths
    WEIGHTS_DIR = BASE_DIR / 'weights'
    STATIC_DIR = BASE_DIR / 'app' / 'static'
    CAPTURES_DIR = STATIC_DIR / 'captures'
    TEMPLATES_DIR = BASE_DIR / 'app' / 'templates'
    
    # Camera Configuration
    RTSP_URL = os.environ.get('RTSP_URL') or 'rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1'
    CAMERA_SOURCE_TYPE = 'rtsp'  # 'rtsp' | 'upload' | 'webcam'
    
    # Model Configuration
    YOLO_COUNTING_MODEL = WEIGHTS_DIR / 'yolo_counting_nano.onnx'
    YOLO_DEFECT_MODEL = WEIGHTS_DIR / 'yolo_defect_detection.onnx'
    SAM2_MODEL = WEIGHTS_DIR / 'sam2_hiera_tiny.pt'
    
    # Detection Settings
    DETECTION_CONFIDENCE_THRESHOLD = 0.8
    COUNTING_FPS_TARGET = 25
    
    # Session Configuration
    MAX_SESSIONS = 100
    AUTO_CLEANUP_OLD_SESSIONS = True
    SESSIONS_INDEX_FILE = CAPTURES_DIR / 'sessions_index.json'
    
    # UI Theme
    PRIMARY_COLOR = '#003473'
    THEME = 'dark'
    
    # Video Streaming
    MJPEG_QUALITY = 85
    STREAM_FPS = 25
    
    # Hardware
    USE_GPU = True
    GPU_DEVICE = 0


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    
# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(env='default'):
    """Get configuration based on environment"""
    return config.get(env, config['default'])
