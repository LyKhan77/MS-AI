#!/bin/bash

# Metal Sheet AI Inspection System - Deployment Script
# Deploy from macOS to Jetson Orin Nano

echo "🚀 Metal Sheet AI Inspection System - Jetson Deployment"
echo "=================================================="

# Configuration
JETSON_IP="192.168.2.122"
JETSON_USER="lee"
JETSON_PATH="/home/lee/ms_aims_streamlit"
LOCAL_PATH="/Users/leekhan/project/CV/metalDetector/ms_aims_streamlit"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check SSH connection
print_status "Checking SSH connection to Jetson..."
if ! ssh -o ConnectTimeout=5 $JETSON_USER@$JETSON_IP "echo 'Connection successful'" 2>/dev/null; then
    print_error "Cannot connect to Jetson at $JETSON_IP"
    echo "Please ensure:"
    echo "1. Jetson is powered on and connected to network"
    echo "2. SSH is enabled on Jetson"
    echo "3. You can manually connect: ssh $JETSON_USER@$JETSON_IP"
    exit 1
fi

print_status "SSH connection successful!"

# Create deployment directory
print_status "Creating deployment directory on Jetson..."
ssh $JETSON_USER@$JETSON_IP "mkdir -p $JETSON_PATH"

# Sync files to Jetson (exclude large files and cache)
print_status "Syncing files to Jetson..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='data/outputs_*' \
    --exclude='models/sam3/*' \
    --exclude='.DS_Store' \
    $LOCAL_PATH/ $JETSON_USER@$JETSON_IP:$JETSON_PATH/

# Set up Jetson environment
print_status "Setting up Jetson environment..."
ssh $JETSON_USER@$JETSON_IP << 'EOF'
cd ~/ms_aims_streamlit
chmod +x run_jetson.sh
chmod +x jetson_setup.py

# Create necessary directories
mkdir -p data/inputs data/outputs_ng data/outputs_ok data/logs models/sam3
EOF

# Check Jetson status
print_status "Checking Jetson system status..."
echo "Jetson System Information:"
ssh $JETSON_USER@$JETSON_IP << 'EOF'
echo "==============================="
echo "Jetson Model:"
cat /proc/device-tree/model 2>/dev/null || echo "Unknown"
echo "Python version:"
python3 --version
echo "CUDA status:"
python3 -c "import torch; print('CUDA Available:', torch.cuda.is_available())" 2>/dev/null || echo "PyTorch not installed"
echo "GPU info:"
python3 -c "import torch; print('GPU:', torch.cuda.get_device_name(0))" 2>/dev/null || echo "GPU not detected"
echo "Memory info:"
free -h | head -2
echo "==============================="
EOF

print_warning "Deployment completed!"
echo ""
echo "Next steps on Jetson:"
echo "1. SSH to Jetson: ssh $JETSON_USER@$JETSON_IP"
echo "2. Go to project: cd ms_aims_streamlit"
echo "3. Run setup: ./run_jetson.sh"
echo "4. Access app: http://$JETSON_IP:8501"
echo ""
print_status "For detailed setup instructions, see: JETSON_SETUP.md"

# Optional: Open SSH connection
read -p "Do you want to SSH to Jetson now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Opening SSH connection to Jetson..."
    ssh $JETSON_USER@$JETSON_IP
fi
