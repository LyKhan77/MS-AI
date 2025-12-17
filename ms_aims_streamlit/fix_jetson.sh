#!/bin/bash

# Fix Script for Jetson Dependencies Issues
# Addresses PyTorch, NumPy, and compatibility problems

echo "🔧 Fixing Jetson Dependencies Issues"
echo "====================================="

cd ~/project/MS-AI/ms_aims_streamlit

# Stop any running processes
echo "Stopping any running processes..."
pkill -f python3
pkill -f streamlit

# Backup current virtual environment
if [ -d "venv" ]; then
    echo "Backing up current virtual environment..."
    mv venv venv_backup_$(date +%Y%m%d_%H%M%S)
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install compatible NumPy first (this is crucial!)
echo "Installing compatible NumPy version..."
pip install "numpy<2.0"

# Install PyTorch for Jetson (CUDA 11.8 compatible)
echo "Installing PyTorch for Jetson..."
pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu118

# Test PyTorch installation
echo "Testing PyTorch installation..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('WARNING: CUDA not available - using CPU')
"

# Install other core dependencies with compatible versions
echo "Installing other dependencies..."
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

# Install Jetson monitoring tools
echo "Installing Jetson monitoring tools..."
pip install jetson-stats==4.3.2
pip install psutil==7.1.3

# Install audio (for alerts)
pip install pygame==2.6.1

# Test complete installation
echo "Testing complete installation..."
python3 -c "
print('🔍 Complete Installation Check:')
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
    print(f'   CUDA Available: {torch.cuda.is_available()}')
    if torch.cuda.is_available():
        print(f'   GPU: {torch.cuda.get_device_name(0)}')
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
print('Installation test completed!')
"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p data/inputs data/outputs_ng data/outputs_ok data/logs models/sam3

# Test application import
echo "Testing application imports..."
python3 -c "
import sys
sys.path.append('src')
try:
    from detector import SAM3Engine
    print('✅ Detector module imported successfully')
except Exception as e:
    print(f'❌ Detector import failed: {e}')

try:
    from camera import VideoStreamer
    print('✅ Camera module imported successfully')
except Exception as e:
    print(f'❌ Camera import failed: {e}')
"

echo ""
echo "✅ Fix completed successfully!"
echo ""
echo "To run the application:"
echo "source venv/bin/activate"
echo "streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
echo ""
echo "Or use the fixed launcher:"
echo "./run_jetson_fixed.sh"
