# Metal Sheet QC Detection System

AI-powered Quality Control system for metal sheet detection, counting, and defect analysis on NVIDIA Jetson Orin Nano.

## Features

- **Real-time Counting**: Automatic metal sheet counting with RTSP camera support
- **Defect Detection**: Surface defect identification using YOLO + SAM2
- **Dimension Measurement**: Pixel-to-metric dimension calculation
- **Dark Theme UI**: Modern web interface with primary color #003473

## Hardware Requirements

- NVIDIA Jetson Orin Nano (8GB)
- JetPack 6.0 (R36.4.7)
- CUDA 12.6
- IP Camera with RTSP support

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd MS-Detector
```

### 2. Setup Environment on Jetson

```bash
# Make setup script executable
chmod +x setup_jetson.sh

# Run setup script
./setup_jetson.sh
```

This will:

- Create Python virtual environment
- Install PyTorch for Jetson (CUDA 12.6)
- Install all dependencies
- Install SAM2 from source
- Create necessary directories
- Verify installation

### 3. Download Model Weights

```bash
# Download SAM2 checkpoint
wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt -P weights/

# YOLO models will be downloaded automatically on first use
# Or manually place your trained models in weights/ directory
```

### 4. Configure Environment

```bash
# Copy example .env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 5. Test RTSP Camera

```bash
# Activate virtual environment
source venv/bin/activate

# Test camera connection
python scripts/test_rtsp.py
```

### 6. Run Application

```bash
# Activate virtual environment if not already activated
source venv/bin/activate

# Run Flask application
python run.py
```

Access the web interface at: `http://<jetson-ip>:5000`

## Project Structure

```
MS-Detector/
├── app/
│   ├── __init__.py               # Flask app factory
│   ├── config.py                 # Configuration
│   ├── routes/                   # Web routes
│   ├── services/                 # Business logic
│   ├── static/                   # Static files (CSS, JS, captures)
│   └── templates/                # HTML templates
├── weights/                      # AI model weights
├── scripts/                      # Utility scripts
├── requirements.txt              # Python dependencies
├── setup_jetson.sh              # Setup script
├── test_environment.py          # Environment verification
└── run.py                        # Application entry point
```

## Development Workflow

1. **Phase 1: Real-time Counting**

   - Train/download YOLO model for metal sheet detection
   - Implement counting logic with state machine
   - Build dashboard UI

2. **Phase 2: Defect Detection**

   - Train YOLO on NEU-DET dataset
   - Integrate SAM2 for segmentation
   - Build analysis UI

3. **Phase 3: Dimension Measurement**
   - Implement calibration
   - Add measurement algorithm

## Testing

```bash
# Test environment setup
python test_environment.py

# Test RTSP camera
python scripts/test_rtsp.py --rtsp-url "your_rtsp_url"

# Run Flask app in development mode
FLASK_ENV=development python run.py
```

## Configuration

Edit `app/config.py` or set environment variables in `.env`:

- `RTSP_URL`: Camera RTSP stream URL
- `DETECTION_CONFIDENCE_THRESHOLD`: Minimum confidence for detection (default: 0.8)
- `PRIMARY_COLOR`: UI primary color (default: #003473)

## API Endpoints

### Session Management

- `POST /api/session/start` - Start counting session
- `POST /api/session/finish` - Finish session
- `GET /api/session/status` - Get current status

### Camera Control

- `POST /api/camera/set_rtsp` - Update RTSP URL
- `POST /api/camera/upload_video` - Upload video file

### Video Stream

- `GET /video_feed` - MJPEG video stream

## Troubleshooting

### CUDA Not Available

```bash
# Check CUDA installation
nvcc --version
nvidia-smi

# Verify PyTorch sees CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### RTSP Connection Issues

- Verify camera IP and credentials
- Check network connectivity
- Ensure firewall allows RTSP (port 554)

### Low FPS

- Reduce camera resolution in camera settings
- Check network bandwidth
- Verify GPU is being used for inference

## Production Deployment

For production, use Gunicorn:

```bash
gunicorn --workers=1 --threads=4 --bind 0.0.0.0:5000 run:app
```

## License

[Your License]

## Contributors

[Your Name/Team]

## Acknowledgments

- Ultralytics YOLOv8
- Meta SAM2 (Segment Anything Model 2)
- NEU-DET Dataset (Northeastern University)
