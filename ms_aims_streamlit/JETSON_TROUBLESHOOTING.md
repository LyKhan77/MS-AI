# Jetson Orin Nano Troubleshooting Guide

## Quick Solutions for Common Issues

### ❌ ModuleNotFoundError: No module named 'streamlit'

**Problem:** Dependencies not installed in virtual environment

**Solution 1: Use the installer script**
```bash
cd ~/ms_aims_streamlit
./install_jetson.sh
```

**Solution 2: Manual installation**
```bash
cd ~/ms_aims_streamlit
source venv/bin/activate
pip install streamlit opencv-python-headless numpy torch torchvision
```

**Solution 3: Recreate virtual environment**
```bash
cd ~/ms_aims_streamlit
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements_jetson.txt
```

### ❌ CUDA not available

**Problem:** PyTorch not installed with CUDA support

**Check CUDA version:**
```bash
nvcc --version
```

**Install correct PyTorch:**
```bash
# For JetPack 5.1 (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For JetPack 5.0 (CUDA 11.4)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu114
```

**Test CUDA:**
```bash
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

### ❌ Permission denied for sudo commands

**Problem**: User not in sudoers or password required

**Solution 1**: Run without sudo (performance mode optional)
```bash
./run_jetson.sh  # Will work without performance mode
```

**Solution 2**: Configure passwordless sudo
```bash
sudo visudo
# Add this line at the end:
lee ALL=(ALL) NOPASSWD: ALL
```

### ❌ Display not working

**Problem**: X11 server not configured

**Check display:**
```bash
echo $DISPLAY
export DISPLAY=:0
```

**Start X11 server:**
```bash
sudo systemctl start gdm3
# or
startx
```

**Use headless mode:**
```bash
export DISPLAY=""
python3 app.py --server.headless true
```

### ❌ Low performance / High latency

**Problem**: Not using maximum performance mode

**Set maximum performance:**
```bash
sudo nvpmodel -m 0
sudo jetson_clocks
```

**Check current mode:**
```bash
sudo nvpmodel -q
```

**Monitor performance:**
```bash
sudo apt install jetson-stats
jtop
```

### ❌ Camera not working

**Problem**: Camera permissions or configuration

**Check camera device:**
```bash
ls /dev/video*
```

**Test camera with OpenCV:**
```bash
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera working')
    cap.release()
else:
    print('❌ Camera not working')
"
```

**Fix permissions:**
```bash
sudo usermod -a -G video $USER
# Reboot required
```

### ❌ Network access issues

**Problem**: Cannot access web interface remotely

**Check IP address:**
```bash
hostname -I | awk '{print $1}'
```

**Open firewall:**
```bash
sudo ufw allow 8501
sudo ufw status
```

**Check if Streamlit is running:**
```bash
netstat -tlnp | grep :8501
ps aux | grep streamlit
```

### ❌ Memory issues

**Problem**: Out of memory errors

**Check GPU memory:**
```bash
python3 -c "
import torch
print('GPU Memory:', torch.cuda.get_device_properties(0).total_memory / 1024**3, 'GB')
print('Allocated:', torch.cuda.memory_allocated() / 1024**3, 'GB')
"
```

**Clear GPU cache:**
```bash
python3 -c "import torch; torch.cuda.empty_cache()"
```

**Reduce model size:**
```python
# In detector.py, reduce image size
config.image_size = 560
```

## Performance Optimization

### Enable Maximum Performance
```bash
# Set to maximum power mode
sudo nvpmodel -m 0

# Enable maximum clocks
sudo jetson_clocks

# Set GPU frequencies (optional)
echo 1100000 | sudo tee /sys/devices/gpu.0/devfreq/gpu.0/max_freq
```

### Monitor System Resources
```bash
# Install monitoring tools
sudo pip install jetson-stats
sudo apt install htop

# Run monitoring
jtop
htop
tegrastats
```

### Optimize Memory Usage
```bash
# Set environment variables
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export CUDA_VISIBLE_DEVICES=0

# Check memory usage
free -h
cat /proc/meminfo | grep MemTotal
```

## Debugging Mode

### Run with Detailed Logging
```bash
cd ~/ms_aims_streamlit
source venv/bin/activate

# Enable debug mode
python3 -u app.py --logger.level debug
```

### Test Individual Components
```bash
# Test imports
python3 -c "
try:
    import streamlit; print('✅ Streamlit')
except Exception as e: print('❌ Streamlit:', e)

try:
    import torch; print('✅ PyTorch', torch.__version__)
    print('  CUDA:', torch.cuda.is_available())
except Exception as e: print('❌ PyTorch:', e)

try:
    import cv2; print('✅ OpenCV', cv2.__version__)
except Exception as e: print('❌ OpenCV:', e)
"
```

### Check Configuration
```bash
# Check .streamlit/config.toml
cat .streamlit/config.toml

# Check environment variables
env | grep -E "(CUDA|DISPLAY|PYTHONPATH)"
```

## Recovery Procedures

### Reset Virtual Environment
```bash
cd ~/ms_aims_streamlit
rm -rf venv
python3 -m venv venv
source venv/bin/activate
./install_jetson.sh
```

### Reset Jetson Performance
```bash
# Reset to default mode
sudo nvpmodel -m 1

# Then set back to max mode
sudo nvpmodel -m 0
sudo jetson_clocks
```

### Clear All Cache
```bash
# Python cache
find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# pip cache
pip cache purge

# Clear Jetson stats cache
jtop --reset
```

## Support

### Log Files
```bash
# Streamlit logs
tail -f ~/.streamlit/logs/streamlit.log

# System logs
journalctl -u gdm3 -f
dmesg | tail -f

# Application logs
python3 app.py 2>&1 | tee app.log
```

### Get Help
1. Check this troubleshooting guide first
2. Look at application logs for specific error messages
3. Monitor system resources with `jtop`
4. Check Jetson documentation: https://developer.nvidia.com/embedded/jetson

### Contact Information
For technical support:
- Check system status: `jtop`
- Review error messages in logs
- Provide Jetson model and JetPack version
- Include steps to reproduce the issue
