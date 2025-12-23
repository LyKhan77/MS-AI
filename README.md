# MS Detector v2 - QC Dashboard

## Overview

This is a Quality Control Dashboard for Metal Sheet Detection, Counting, and Defect Analysis using AI.

- **Real-Time Counting**: Uses **YOLOv11m** (custom trained) + **SORT** tracking to detect and count unique metal sheets.
- **Defect Analysis**: Uses **SAM-3** (Segment Anything) for post-session defect detection.
- **Defect Types**: Scratches, dents, rust, holes, coating bubbles.
- **Severity Classification**: Minor, moderate, critical based on defect area.
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

- **Camera Source**: By default uses Webcam `0`. Supports RTSP streams and video file upload via UI.
- **Models**:
  - YOLOv11m: `backend/yolo11m_metalsheet.pt` (custom trained on Roboflow dataset)
  - SAM-3: Loaded from HuggingFace Transformers (`facebook/sam3`)
- **HuggingFace Setup**: Run `huggingface-cli login` or `./hf_login.sh` for SAM-3 access.

## Usage

### Live Detection & Counting

1. Open Dashboard and set camera source (webcam/RTSP or upload video).
2. Enter a **Session Name**, **Max Count**, and **Confidence Threshold**.
3. Click **Start Session**.
4. System counts unique metal sheets using SORT tracking.
5. Captures saved with bounding box crops: `backend/data/sessions/<id>/captures/`.

### Defect Analysis

1. After session completes, go to **Defects** page.
2. Click **Analyze Defects** to run SAM-3 on session captures.
3. View detected defects with severity classification.
4. Export defect crops as ZIP file.

### Session Management

- **Sessions** page: View history with pagination, delete sessions
- Each session stores captures and defect analysis results
- Real-time count tracking during active sessions

## Training YOLOv11m Model

To train a custom YOLOv11m model on the Metal Sheet dataset:

```bash
cd training-model
python train_yolo11m.py
```

Training details:
- Dataset: Roboflow Metal Sheet v6 (single class: metalsheet)
- Model automatically copied to `backend/yolo11m_metalsheet.pt` after training
- GPU Memory: ~6-8GB VRAM (batch=16)
