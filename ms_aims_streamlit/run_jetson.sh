#!/bin/bash

# Metal Sheet AI Inspection System - Jetson Orin Nano Launcher

echo "🚀 Metal Sheet AI Inspection System - Jetson Orin Nano"
echo "=================================================="

# Set performance mode
echo "⚡ Setting performance mode..."
sudo nvpmodel -m 0 2>/dev/null || echo "nvpmodel not available"
sudo jetson_clocks 2>/dev/null || echo "jetson_clocks not available"

# Set display environment
export DISPLAY=:0

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.10 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
python3 jetson_setup.py

# Set CUDA optimizations
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Run the application with Jetson optimizations
echo "Starting Metal Sheet AI Inspection System..."
echo "Application will be available at: http://localhost:8501"
echo "Or access remotely: http://$(hostname -I | awk '{print $1}'):8501"

# Start with optimized settings
python3 -u app.py \
    --server.headless false \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --browser.gatherUsageStats false \
    --server.maxUploadSize 200
