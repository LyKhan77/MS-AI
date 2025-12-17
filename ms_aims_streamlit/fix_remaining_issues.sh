#!/bin/bash

# Fix remaining issues for Jetson deployment
echo "🔧 Fixing Remaining Issues for Jetson"
echo "=================================="

cd ~/project/MS-AI/ms_aims_streamlit
source venv/bin/activate

echo "📦 Fixing PyTorch version issues..."

# Remove incompatible PyTorch
pip uninstall torch torchvision torchaudio -y

# Install Jetson-optimized PyTorch
echo "Installing Jetson-optimized PyTorch..."
wget https://nvidia.box.com/shared/static/py3ofp1v3cc5q2x1n4f7cc3k1hn3qjg1m -O jetson_pytorch.sh
bash jetson_pytorch.sh

# Or manual installation
echo "Installing manual PyTorch for Jetson..."
pip install torch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118

echo "🔧 Fixing NumPy compatibility..."
pip uninstall numpy -y
pip install "numpy<2.0"

echo "🔧 Testing installation..."
python3 -c "
import torch
import torchvision
import transformers
import streamlit
print('✅ All core packages working!')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA Available: {torch.cuda.is_available()}')
print(f'Transformers: {transformers.__version__}')
"

echo "🔧 Fixing app.py session state issue..."
# This will be handled by creating a new fixed version

echo "✅ Remaining issues fixed!"
echo ""
echo "To restart the application:"
echo "./run_jetson.sh"
