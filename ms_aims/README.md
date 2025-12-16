# Metal Sheet AI Monitor (MS-AIM)

An AI-powered computer vision system for monitoring and quality control of metal sheets using NVIDIA Jetson Orin Nano.

## Overview
This system automates dimension measurement and defect detection for manual metal sheet work stations.

## Project Structure
- `src/`: Core logic (AI, Camera, UI)
- `configs/`: Configuration files
- `data/`: Logs and captured images
- `main.py`: Entry point

## Installation

### 1. Jetson Orin Nano (Production)
**Recommended Python Version:** Python 3.10 (Default on JetPack 6)

#### A. Standard Installation (Fresh Setup)
1. **Create Virtual Environment**
   It is crucial to use `--system-site-packages` to access pre-installed JetPack libraries (TensorRT, CUDA).
   ```bash
   # Install venv module if missing
   sudo apt-get install python3-venv

   # Create venv
   python3 -m venv .venv --system-site-packages

   # Activate venv
   source .venv/bin/activate
   ```

2. **Run Setup Script**
   Run the automated setup script to install PyTorch/OpenCV with CUDA support.
   ```bash
   chmod +x setup_jetson.sh
   ./setup_jetson.sh
   ```

#### B. Advanced / Existing Environment
If you already have PyTorch/TensorRT installed (e.g. from a custom image or previous setup), use the minimal script to avoid conflicts:
```bash
chmod +x setup_jetson_minimal.sh
./setup_jetson_minimal.sh
```

### 2. Local Development (Mac/PC)
For testing logic without GPU acceleration:
```bash
pip install -r requirements.txt
pip install opencv-python  # Manually install CPU opencv for dev
```

## Usage
Run the application:
```bash
python3 main.py
```
Access dashboard at `http://<device-ip>:8080`
