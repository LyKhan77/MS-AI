#!/usr/bin/env python3
"""
Jetson Orin Nano setup script for Metal Sheet AI Inspection System
Optimized for GPU acceleration and Jetson hardware
"""

import subprocess
import sys
import os

def run_command(cmd, check=True):
    """Run shell command and return result"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def check_jetson_environment():
    """Check Jetson environment and CUDA"""
    print("🔧 Checking Jetson Environment...")
    print("=" * 50)
    
    # Check Jetson platform
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip()
            print(f"✅ Jetson Model: {model}")
    except:
        print("⚠️ Could not detect Jetson model")
    
    # Check CUDA
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA Available: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            return True
        else:
            print("❌ CUDA not available")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def install_jetson_packages():
    """Install Jetson-specific packages"""
    print("\n📦 Installing Jetson packages...")
    
    packages = [
        "jetson-stats",
        "py-cpuinfo",
        "psutil",
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        run_command(f"pip3 install {package}")

def setup_jetson_optimizations():
    """Setup Jetson performance optimizations"""
    print("\n⚡ Setting up Jetson optimizations...")
    
    # Set maximum performance mode
    print("Setting Jetson to maximum performance mode...")
    run_command("sudo nvpmodel -m 0", check=False)  # Maximum performance
    run_command("sudo jetson_clocks", check=False)   # Maximum clocks
    
    # Configure power settings
    print("Optimizing power settings...")
    run_command("echo 850000 | sudo tee /sys/devices/gpu.0/devfreq/gpu.0/min_freq", check=False)
    run_command("echo 1100000 | sudo tee /sys/devices/gpu.0/devfreq/gpu.0/max_freq", check=False)

def setup_display_environment():
    """Setup display environment for Streamlit"""
    print("\n🖥️ Setting up display environment...")
    
    # Set display for GUI applications
    os.environ['DISPLAY'] = ':0'
    
    # Check if display is working
    if run_command("xset q 2>/dev/null", check=False):
        print("✅ Display environment ready")
    else:
        print("⚠️ Display environment may need manual configuration")
        print("   Try: export DISPLAY=:0")

def create_jetson_config():
    """Create Jetson-specific configuration"""
    config_content = """
# Jetson Orin Nano optimizations for MS-AIS

[server]
headless = false
runOnSave = false
port = 8501
maxUploadSize = 200
# Enable CORS for remote access
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
# Use headless Chrome for better performance
serverAddress = "0.0.0.0"

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[client]
toolbarMode = "minimal"
# Optimize for Jetson performance
caching = true

[logger]
level = "info"
"""
    
    with open('.streamlit/config.toml', 'w') as f:
        f.write(config_content)
    
    print("✅ Jetson configuration created")

def main():
    """Main setup function"""
    print("🚀 Jetson Orin Nano Setup for Metal Sheet AI Inspection")
    print("=" * 60)
    
    # Check Jetson environment
    if not check_jetson_environment():
        print("❌ Jetson environment check failed")
        return False
    
    # Install Jetson packages
    install_jetson_packages()
    
    # Setup optimizations
    setup_jetson_optimizations()
    
    # Setup display
    setup_display_environment()
    
    # Create config
    create_jetson_config()
    
    print("\n" + "=" * 60)
    print("✅ Jetson setup completed!")
    print("\n🚀 To start the application:")
    print("   python3 app.py")
    print("   Or: ./run_jetson.sh")
    
    print("\n📊 To monitor Jetson performance:")
    print("   jtop  # Install with: sudo pip3 install jetson-stats")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
