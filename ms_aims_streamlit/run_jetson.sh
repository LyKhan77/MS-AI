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

# Install dependencies
echo "📦 Installing dependencies for Jetson..."
pip install --upgrade pip

# Install PyTorch for Jetson (CUDA 11.8 for JetPack 5.1)
echo "Installing PyTorch for Jetson..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
echo "Installing other packages..."
pip install streamlit>=1.35.0
pip install opencv-python-headless>=4.9.0
pip install numpy>=1.24.0
pip install Pillow>=10.0.0
pip install transformers>=4.45.0
pip install accelerate>=0.34.0
pip install supervision>=0.22.0
pip install scikit-image>=0.22.0
pip install pygame>=2.5.0
pip install pydantic>=2.5.0
pip install python-dotenv>=1.0.0
pip install tqdm>=4.66.0

# Install Jetson-specific packages
echo "Installing Jetson-specific packages..."
pip install jetson-stats py-cpuinfo psutil

# Check if everything is installed correctly
echo "🔧 Checking installation..."
python3 -c "
import streamlit
import cv2
import numpy as np
import torch
import transformers
print('✅ All core dependencies installed successfully!')
print(f'   Streamlit: {streamlit.__version__}')
print(f'   OpenCV: {cv2.__version__}')
print(f'   PyTorch: {torch.__version__}')
print(f'   CUDA Available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'   GPU: {torch.cuda.get_device_name(0)}')
print(f'   Transformers: {transformers.__version__}')
"

# Set CUDA optimizations
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Run the application with Jetson optimizations
echo "Starting Metal Sheet AI Inspection System..."
echo "Application will be available at: http://localhost:8501"
echo "Or access remotely: http://$(hostname -I | awk '{print $1}'):8501"

# Check if everything is installed correctly first
echo "🔧 Checking installation before starting..."
python3 -c "
import sys
import os
sys.path.append(os.getcwd())

try:
    import streamlit
    import cv2
    import numpy as np
    import torch
    import transformers
    from detector import SAM3Engine
    
    print('✅ All dependencies verified successfully!')
    print(f'   Streamlit: {streamlit.__version__}')
    print(f'   PyTorch: {torch.__version__} (CUDA: {torch.cuda.is_available()})')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('Please run ./fix_jetson.sh first')
    sys.exit(1)
except Exception as e:
    print(f'❌ Other error: {e}')
    print('Please check installation')
    sys.exit(1)
"

# Set CUDA optimizations
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Run the application with Jetson optimizations using streamlit run
echo "Starting Metal Sheet AI Inspection System..."
echo "Application will be available at: http://localhost:8501"
echo "Or access remotely: http://$(hostname -I | awk '{print $1}'):8501"

# Start with streamlit run command
streamlit run app.py \
    --server.headless false \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --browser.gatherUsageStats false \
    --server.maxUploadSize 200 \
    --server.fileWatcherType none
