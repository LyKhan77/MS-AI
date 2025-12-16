#!/bin/bash
# Minimal Installation script for Existing Jetson Environments (JetPack 6.x)
# Use this if you already have PyTorch/TensorRT/CUDA installed.

set -e

echo "Starting MS-AIM Minimal Setup..."

# 0. Check for Virtual Environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "\033[0;31mWARNING: No virtual environment detected!\033[0m"
    echo "Please ensure you are in your active venv (with --system-site-packages)."
    read -p "Proceed anyway? (y/N) " proceed
    if [[ "$proceed" != "y" && "$proceed" != "Y" ]]; then
        exit 1
    fi
fi

# 1. System Dependencies (Safe to run, apt skips if installed)
echo "[1/3] Checking System Dependencies..."
sudo apt-get update
sudo apt-get install -y \
    libjpeg-dev zlib1g-dev libpython3-dev \
    libavcodec-dev libavformat-dev libswscale-dev

# 2. Python Dependencies (Missing only)
echo "[2/3] Installing Missing Python Libraries (NiceGUI, etc)..."
# We exclude things that might conflict with system packages
pip install nicegui pyserial

# 3. OpenCV Check
echo "[3/3] Checking OpenCV..."
if python3 -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())" 2>/dev/null; then
    echo -e "\033[0;32mOpenCV CUDA support detected!\033[0m"
else
    echo -e "\033[0;33mWARNING: Standard OpenCV (CPU) detected or CUDA check failed.\033[0m"
    echo "For production performance, consider building OpenCV with CUDA."
    echo "However, the system will run fine for development."
fi

echo "Minimal Setup Complete!"
