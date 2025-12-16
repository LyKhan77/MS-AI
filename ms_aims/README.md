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
Run the automated setup script to install PyTorch/OpenCV with CUDA support and other dependencies.
```bash
chmod +x setup_jetson.sh
./setup_jetson.sh
```
*Note: Building OpenCV from source can take 1-2 hours.*

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
