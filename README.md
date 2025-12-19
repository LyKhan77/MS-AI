# MS Detector v2 - QC Dashboard

## Overview

This is a Quality Control Dashboard for Metal Sheet Detection and Counting using AI.

- **Real-Time Counting**: Uses **YOLO-World** (Zero-shot) to detect sheets.
- **Defect Analysis**: Uses **SAM 3** (Segment Anything) for detailed inspection.
- **Frontend**: React (Vite) + Tailwind CSS.
- **Backend**: Flask + SocketIO.

## Installation (On Remote GPU Machine)

### 1. Backend Setup

Prerequisites: Python 3.9+, CUDA drivers for RTX 4090.

```bash
cd backend
# 1. Create and Activate Virtual Environment (Highly Recommended)
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On Linux/tvOS/macOS:
source venv/bin/activate

# 2. Install PyTorch with CUDA 12.6 (Best for RTX 5080/4090 + CUDA 12.8 Host)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# 3. Install other dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

Prerequisites: Node.js 18+.

```bash
cd frontend
npm install
```

## Running the Application

### 1. Start Backend

```bash
cd backend
python app.py
```

_Server runs on `http://0.0.0.0:5000`_

### 2. Start Frontend

```bash
cd frontend
npm run dev
```

_UI runs on `http://localhost:5173`_

## Configuration

- **Camera Source**: By default uses Webcam `0`. You can change this in the UI or in `backend/config.py` (`RTSP_URL`).
- **Models**: code expects `yolov8s-world.pt` (auto-downloads) and a SAM 3 checkpoint.

## Usage

1. Open the Dashboard.
2. Enter a **Session Name** and **Max Count**.
3. Click **Start Session**.
4. The system will count sheets seen by the camera.
5. Captures are saved in `backend/data/sessions/<id>/captures`.
