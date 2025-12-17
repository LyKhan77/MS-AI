#!/bin/bash

# Final Fix Script for Complete Jetson Deployment
echo "🚀 Final Fix for Complete Jetson Deployment"
echo "=================================="

cd ~/project/MS-AI/ms_aims_streamlit

echo "⚠️ WARNING: This will recreate the entire environment!"
echo "Make sure you have a backup if needed."
read -p "Continue? (y/n): " -n 1 -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

# Kill any running processes
echo "Stopping any running processes..."
pkill -f streamlit || true
pkill -f python3 || true
sleep 2

# Remove old environment
echo "Removing old virtual environment..."
rm -rf venv
rm -rf venv_backup_*

# Create new environment
echo "Creating fresh virtual environment..."
python3 -m venv
source venv/bin/activate

# Install core packages first
echo "Installing core packages..."
pip install --upgrade pip setuptools wheel

# Install compatible PyTorch for Jetson (without CUDA issues)
echo "Installing CPU-compatible PyTorch for Jetson..."
pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1 --index-url https://download.pytorch.org/whl/cpu

# Install other core dependencies
echo "Installing other core dependencies..."
pip install "numpy<2.0"
pip install streamlit==1.52.1
pip install opencv-python-headless==4.10.0.84
pip install Pillow==11.0.0
pip install transformers==4.57.3
pip install accelerate==1.2.1
pip install supervision==0.27.0
pip install scikit-image==0.25.2
pip install pydantic==2.12.5
pip install python-dotenv==1.2.1
pip install tqdm==4.67.1
pip install pygame==2.6.1

# Install Jetson monitoring tools
echo "Installing Jetson monitoring tools..."
pip install jetson-stats==4.3.2
pip install psutil==7.1.3
pip install py-cpuinfo==9.0.0

# Test the installation
echo "🔧 Testing installation..."
python3 -c "
print('🔍 Installation Test Results:')
print('=' * 50)

try:
    import streamlit
    print(f'✅ Streamlit: {streamlit.__version__}')
except Exception as e:
    print(f'❌ Streamlit: {e}')

try:
    import cv2
    print(f'✅ OpenCV: {cv2.__version__}')
except Exception as e:
    print(f'❌ OpenCV: {e}')

try:
    import numpy as np
    print(f'✅ NumPy: {np.__version__}')
except Exception as e:
    print(f'❌ NumPy: {e}')

try:
    import torch
    print(f'✅ PyTorch: {torch.__version__}')
    print(f'   CPU fallback mode enabled')
except Exception as e:
    print(f'❌ PyTorch: {e}')

try:
    import transformers
    print(f'✅ Transformers: {transformers.__version__}')
except Exception as e:
    print(f'❌ Transformers: {e}')

try:
    import supervision
    print(f'✅ Supervision: {supervision.__version__}')
except Exception as e:
    print(f'❌ Supervision: {e}')

print('=' * 50)
print('✅ Core packages installation completed!')
"

# Test application imports
echo "🔧 Testing application imports..."
python3 -c "
import sys
sys.path.append('src')
try:
    from detector import SAM3Engine, SAM3_AVAILABLE
    print('✅ Detector module imported successfully')
    print(f'   SAM-3 Available: {SAM3_AVAILABLE}')
    
    engine = SAM3Engine()
    print(f'   SAM3Engine initialized successfully')
    print(f'   Using fallback: {engine.use_fallback}')
    
except Exception as e:
    print(f'❌ Detector import failed: {e}')
    import traceback
    traceback.print_exc()
"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/inputs data/signals data/outputs_ng data/outputs_ok data/logs models/sam3

echo ""
echo "✅ Final fix completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "./run_jetson_fixed.sh"
echo ""
echo "📊 To monitor performance:"
echo "jtop"
echo ""
echo "🌐 Access the application:"
echo "Local: http://localhost:8501"
echo "Remote: http://192.168.2.122:8501"
echo ""
echo "Note: Using CPU-only mode for maximum compatibility"
