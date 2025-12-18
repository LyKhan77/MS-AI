#!/bin/bash

###############################################################################
# Jetson Orin Nano Environment Setup Script
# For Metal Sheet QC Detection System
# JetPack 6.0 (R36.4.7) with CUDA 12.6
###############################################################################

set -e  # Exit on error

echo "=================================================="
echo "Metal Sheet QC Detection - Jetson Setup"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running on Jetson
print_status "Checking Jetson environment..."
if [ -f /etc/nv_tegra_release ]; then
    JETSON_VERSION=$(cat /etc/nv_tegra_release | grep "R36")
    if [ -n "$JETSON_VERSION" ]; then
        print_status "Jetson detected: $JETSON_VERSION"
    else
        print_warning "Different JetPack version detected. Expected R36.x"
    fi
else
    print_error "Not running on Jetson device!"
    exit 1
fi

# Check CUDA availability
print_status "Checking CUDA..."
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $5}' | cut -d',' -f1)
    print_status "CUDA $CUDA_VERSION detected"
else
    print_error "CUDA not found! Please install JetPack."
    exit 1
fi

# Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_status "Python $PYTHON_VERSION detected"

# Create virtual environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at ./$VENV_DIR"
    read -p "Remove and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        print_status "Removed old virtual environment"
    else
        print_status "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    print_status "Virtual environment created at ./$VENV_DIR"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch for Jetson (CUDA 12.6)
print_status "Installing PyTorch for Jetson Orin Nano..."
print_warning "This may take several minutes..."

# Check if PyTorch is already installed
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)")
    print_warning "PyTorch $TORCH_VERSION already installed"
    read -p "Reinstall PyTorch? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Skipping PyTorch installation"
    else
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
    fi
else
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
fi

# Install other dependencies
print_status "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# Install Ultralytics separately with --no-deps to avoid reinstalling PyTorch
print_status "Installing Ultralytics (YOLO) without dependencies..."
pip install ultralytics>=8.1.0 --no-deps

# Install Ultralytics dependencies manually (except torch/torchvision)
print_status "Installing Ultralytics required dependencies..."
pip install ultralytics

# Install SAM2 from source
print_status "Installing SAM2 (Segment Anything Model 2)..."
if [ -d "segment-anything-2" ]; then
    print_warning "SAM2 repository already exists"
else
    git clone https://github.com/facebookresearch/segment-anything-2.git
fi

cd segment-anything-2
pip install -e .
cd ..

print_status "SAM2 installed successfully"

# Create necessary directories
print_status "Creating project directories..."
mkdir -p app/static/captures
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/audio
mkdir -p weights
mkdir -p logs

print_status "Directories created"

# Create empty __init__.py files
touch app/__init__.py
touch app/routes/__init__.py
touch app/services/__init__.py

# Set permissions
chmod -R 755 app/static/captures

# Create .env file if not exists
if [ ! -f ".env" ]; then
    print_status "Creating .env file..."
    cat > .env << EOF
# Environment Configuration
FLASK_ENV=development
SECRET_KEY=change-this-in-production

# Camera Configuration
RTSP_URL=rtsp://admin:gspe-intercon@192.168.0.64:554/Streaming/Channels/1

# Model Paths
SAM2_CHECKPOINT_PATH=./weights/sam2_hiera_tiny.pt
EOF
    print_status ".env file created"
else
    print_warning ".env file already exists"
fi

# Verification
echo ""
echo "=================================================="
echo "Running Environment Verification..."
echo "=================================================="

python3 << EOF
import sys

def test_import(module_name, display_name=None):
    display_name = display_name or module_name
    try:
        __import__(module_name)
        print(f"✓ {display_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ {display_name} import failed: {e}")
        return False

print("\nPython Version:", sys.version)
print()

# Test PyTorch and CUDA
if test_import('torch', 'PyTorch'):
    import torch
    print(f"  PyTorch version: {torch.__version__}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  CUDA version: {torch.version.cuda}")
        print(f"  GPU device: {torch.cuda.get_device_name(0)}")

print()
test_import('cv2', 'OpenCV')
test_import('PIL', 'Pillow')
test_import('numpy', 'NumPy')
test_import('flask', 'Flask')
test_import('ultralytics', 'Ultralytics (YOLO)')

print()
EOF

echo ""
print_status "=================================================="
print_status "Setup Complete!"
print_status "=================================================="
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Download model weights to ./weights/"
echo "  3. Test RTSP camera: python scripts/test_rtsp.py"
echo "  4. Run application: python run.py"
echo ""
print_warning "Don't forget to download SAM2 checkpoint:"
print_warning "  wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt -P weights/"
echo ""
