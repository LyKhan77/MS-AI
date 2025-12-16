#!/bin/bash
# Installation script for Metal Sheet AI Monitor on Jetson Orin Nano (JetPack 6.x)

set -e

echo "Starting MS-AIM Setup for Jetson Orin Nano..."

# 1. System Updates & Dependencies
echo "[1/4] Installing System Dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    libopenblas-base \
    libopenmpi-dev \
    libomp-dev \
    git \
    wget \
    build-essential \
    cmake \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gfortran \
    libatlas-base-dev

# 2. PyTorch & Torchvision (JetPack 6.0 / Python 3.10)
# Note: URLs are based on NVIDIA Jetson Zoo for JetPack 6
echo "[2/4] Installing PyTorch & Torchvision (CUDA enabled)..."
export TORCH_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v60/pytorch/torch-2.1.0a0+41361538.nv23.06-cp310-cp310-linux_aarch64.whl
export TORCHVISION_INSTALL=https://developer.download.nvidia.com/compute/redist/jp/v60/torchvision/torchvision-0.16.1a0+g8c5825a.nv23.10-cp310-cp310-linux_aarch64.whl

pip3 install --no-cache $TORCH_INSTALL
pip3 install --no-cache $TORCHVISION_INSTALL

# 3. OpenCV with CUDA Support
# Using AastaNV's script which is standard for Jetson community
echo "[3/4] Building OpenCV with CUDA support (This may take ~1-2 hours)..."
echo "NOTE: If you already have OpenCV CUDA installed, skip this step."
read -p "Do you want to build OpenCV from source? (y/n) " build_opencv

if [ "$build_opencv" == "y" ]; then
    wget https://raw.githubusercontent.com/AastaNV/JEP/master/script/install_opencv4.8.0_Jetson.sh
    chmod +x install_opencv4.8.0_Jetson.sh
    ./install_opencv4.8.0_Jetson.sh
else
    echo "Skipping OpenCV build."
fi

# 4. Python Dependencies
echo "[4/4] Installing Python Libraries..."
pip3 install -r requirements.txt

echo "Setup Complete! Please reboot your Jetson."
