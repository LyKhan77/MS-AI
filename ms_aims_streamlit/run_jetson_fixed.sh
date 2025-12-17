#!/bin/bash

# Metal Sheet AI Inspection System - Jetson Orin Nano (FIXED VERSION)
echo "🚀 Metal Sheet AI Inspection System - Jetson Orin Nano (FIXED VERSION)"
echo "========================================================"

# Set performance mode (with error handling)
echo "⚡ Setting performance mode..."
sudo nvpmodel -m 0 2>/dev/null || echo "nvpmodel not available (continuing...)"
sudo jetson_clocks 2>/dev/null || echo "jetson_clocks not available (continuing...)"

# Set display environment
export DISPLAY=:0

# Check and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./final_fix_jetson.sh first!"
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Simple dependency check
echo "📦 Checking dependencies..."
python3 -c "
try:
    import streamlit
    import cv2
    print('✅ Core dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit 1)

try:
    from detector import SAM3Engine
    print('✅ Detector module available')
except ImportError as e:
    print(f'❌ Detector module issue: {e}')
    exit 1)

try:
    from camera import VideoStreamer
    print('✅ Camera module available')
except ImportError as e:
    print(f'❌ Camera module issue: {e}')
    exit 1)
except Exception as e:
    print(f'❌ Other import error: {e}')
    import traceback
    traceback.print_exc()

# Set CUDA optimizations (will gracefully ignore if CUDA not available)
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Create necessary directories if needed
mkdir -p data/inputs data/outputs_ng data/outputs_ok data/logs models/sam3

# Set configuration
cat > .streamlit/config.toml << 'EOF'
[server]
headless = false
runOnSave = false
port = 8501
maxUploadSize = 200
server.address = "0.0.0.0"

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[client]
toolbarMode = "minimal"
use_column_width = false
width = 1000

[logger]
level = "info"
EOF

# Run the application with proper error handling
echo "🚀 Starting Metal Sheet AI Inspection System..."
echo "Application will be available at: http://localhost:8501"
echo "Or access remotely: http://$(hostname -I | awk '{print $1}')"

# Use streamlit run with error handling
if streamlit run app.py 2>&1 | tee app.log; then
    echo "✅ Application started successfully!"
    echo "Check browser at: http://localhost:8501"
else
    echo "❌ Failed to start application"
    echo "Check logs: tail -50 app.log"
    exit 1
fi
