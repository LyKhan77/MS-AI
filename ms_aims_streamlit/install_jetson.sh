#!/bin/bash

# Metal Sheet AI Inspection System - Jetson Dependencies Installer
# Standalone installation script for debugging

echo "🔧 Jetson Dependencies Installer"
echo "================================="

# Check Python version
echo "Checking Python version..."
python3 --version

# Check if venv exists, create if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install basic dependencies first
echo "Installing basic dependencies..."
pip install setuptools wheel

# Install PyTorch for Jetson
echo "Installing PyTorch for Jetson (this may take a while)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Test PyTorch installation
echo "Testing PyTorch..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
else:
    print('CUDA not available - using CPU')
"

# Install other packages
echo "Installing Streamlit and other packages..."
pip install streamlit
pip install opencv-python-headless
pip install numpy
pip install Pillow
pip install transformers
pip install accelerate
pip install supervision
pip install scikit-image
pip install pygame
pip install pydantic
pip install python-dotenv
pip install tqdm

# Install Jetson monitoring tools
echo "Installing Jetson monitoring tools..."
pip install jetson-stats
pip install py-cpuinfo
pip install psutil

# Final check
echo "Final installation check..."
python3 -c "
print('🔍 Final Dependencies Check:')
print('=' * 40)

try:
    import streamlit
    print(f'✅ Streamlit: {streamlit.__version__}')
except ImportError as e:
    print(f'❌ Streamlit: {e}')

try:
    import cv2
    print(f'✅ OpenCV: {cv2.__version__}')
except ImportError as e:
    print(f'❌ OpenCV: {e}')

try:
    import numpy as np
    print(f'✅ NumPy: {np.__version__}')
except ImportError as e:
    print(f'❌ NumPy: {e}')

try:
    import torch
    print(f'✅ PyTorch: {torch.__version__}')
    print(f'   CUDA: {torch.cuda.is_available()}')
except ImportError as e:
    print(f'❌ PyTorch: {e}')

try:
    import transformers
    print(f'✅ Transformers: {transformers.__version__}')
except ImportError as e:
    print(f'❌ Transformers: {e}')

try:
    import supervision
    print(f'✅ Supervision: {supervision.__version__}')
except ImportError as e:
    print(f'❌ Supervision: {e}')

print('=' * 40)
print('Installation completed!')
"

echo ""
echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. Run: source venv/bin/activate"
echo "2. Run: python3 app.py"
echo "3. Or use: ./run_jetson.sh"
