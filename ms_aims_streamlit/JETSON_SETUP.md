# Jetson Orin Nano Setup Guide

## Overview
This guide provides optimized setup for deploying the Metal Sheet AI Inspection System on NVIDIA Jetson Orin Nano.

## Prerequisites
- Jetson Orin Nano (8GB RAM recommended)
- JetPack SDK 5.1+ installed
- Python 3.10+
- Internet connection

## Quick Start

### 1. Transfer Files to Jetson
```bash
# On your Mac, copy project to Jetson
scp -r /Users/leekhan/project/CV/metalDetector/ms_aims_streamlit lee@192.168.2.122:~/
```

### 2. SSH to Jetson
```bash
ssh lee@192.168.2.122
cd ms_aims_streamlit
```

### 3. Run Jetson Setup
```bash
chmod +x run_jetson.sh
./run_jetson.sh
```

### 4. Access the Application
- **Local**: http://localhost:8501
- **Remote**: http://192.168.2.122:8501

## Manual Setup

### 1. Update Jetson Packages
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install python3-pip python3-venv -y
```

### 2. Setup Virtual Environment
```bash
cd ms_aims_streamlit
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# PyTorch for Jetson (optimized version)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Other dependencies
pip3 install -r requirements.txt

# Jetson-specific packages
pip3 install jetson-stats py-cpuinfo psutil
```

### 4. Configure Jetson Performance
```bash
# Set maximum performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Configure GPU frequencies
echo 850000 | sudo tee /sys/devices/gpu.0/devfreq/gpu.0/min_freq
echo 1100000 | sudo tee /sys/devices/gpu.0/devfreq/gpu.0/max_freq
```

### 5. Setup Display Environment
```bash
export DISPLAY=:0
echo 'export DISPLAY=:0' >> ~/.bashrc
```

### 6. Run Application
```bash
python3 app.py
```

## Jetson Optimizations

### GPU Acceleration
- CUDA-enabled PyTorch for AI inference
- Hardware-accelerated video decoding with GStreamer
- Optimized memory management

### Performance Settings
- Maximum performance mode enabled
- GPU clocks set to maximum
- CUDA memory optimizations

### Video Processing
- GStreamer pipeline for RTSP streams
- Hardware-accelerated video decoding
- Zero-copy frame processing

## Monitoring Performance

### Install Jetson Stats
```bash
sudo pip3 install jetson-stats
sudo jtop
```

### Monitor System Resources
```bash
# GPU utilization
tegrastats

# CPU and memory
htop

# Temperature
sudo tegrastats | grep temp
```

## Troubleshooting

### Display Issues
```bash
# Set display environment
export DISPLAY=:0

# Check X11 server
ps aux | grep X
```

### CUDA Issues
```bash
# Check CUDA installation
nvcc --version
python3 -c "import torch; print(torch.cuda.is_available())"
```

### Performance Issues
```bash
# Check power mode
sudo nvpmodel -q

# Reset to maximum performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Memory Issues
```bash
# Check memory usage
free -h
cat /proc/meminfo | grep MemTotal

# Clear GPU cache
python3 -c "import torch; torch.cuda.empty_cache()"
```

## Configuration

### Streamlit Configuration (Jetson Optimized)
- Server address: 0.0.0.0 (for remote access)
- Headless mode: false
- GPU memory optimization enabled
- Maximum upload size: 200MB

### Hardware Settings
- Power mode: Maximum Performance (15W)
- GPU clocks: Maximum
- CPU governor: Performance
- Memory allocation: Optimized for PyTorch

## Expected Performance

### Processing Times
- **SAM-3 detection**: 500-1500ms (GPU)
- **Fallback detection**: 100-300ms (CPU/GPU)
- **Video processing**: 15-30 FPS

### Resource Usage
- **GPU Memory**: 2-4GB (SAM-3)
- **CPU**: 40-70% during processing
- **Power**: 15W (maximum performance mode)
- **Temperature**: 60-80°C (with proper cooling)

## Network Configuration

### Enable Remote Access
```bash
# Open firewall port
sudo ufw allow 8501

# Check IP address
hostname -I | awk '{print $1}'
```

### RTSP Camera Setup
```bash
# Example RTSP URL format
rtsp://username:password@camera_ip:554/stream_path

# Test RTSP connection
ffplay rtsp://camera_ip/stream
```

## Maintenance

### Regular Updates
```bash
# Update JetPack
sudo apt update && sudo apt upgrade

# Update Python packages
pip install --upgrade -r requirements.txt
```

### Performance Monitoring
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): GPU Temp: $(cat /sys/class/thermal/thermal_zone0/temp | awk '{print $1/1000}')°C"
    echo "$(date): GPU Usage: $(tegrastats | grep GR3D | awk '{print $2}')"
    echo "$(date): RAM Usage: $(free -h | awk '/^Mem:/ {print $3}')"
    sleep 30
done
EOF

chmod +x monitor.sh
./monitor.sh
```

## Tips for Best Performance

1. **Use External Cooling**: Jetson can throttle under load
2. **Maximum Power Mode**: Always use `nvpmodel -m 0`
3. **GPU Optimization**: Enable hardware acceleration in camera settings
4. **Memory Management**: Monitor GPU memory usage
5. **Network Stability**: Use wired Ethernet for RTSP streams
6. **Regular Reboots**: Prevent memory leaks with periodic restarts

## Support

For issues specific to Jetson deployment:
1. Check Jetson forums: https://developer.nvidia.com/embedded/forums
2. Review JetPack documentation
3. Monitor system resources with `jtop`
4. Check thermal management

## Advanced Configuration

### Custom CUDA Settings
```python
# In detector.py, add to __init__:
torch.cuda.set_per_process_memory_fraction(0.8)  # Use 80% of GPU memory
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.enabled = True
```

### Real-time Priority
```bash
# Set real-time priority for application
sudo nice -n -10 python3 app.py
```

### Kernel Optimization
```bash
# Edit /etc/sysctl.conf
vm.swappiness=10
vm.overcommit_memory=1
sudo sysctl -p
```
