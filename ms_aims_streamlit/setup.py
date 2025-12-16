#!/usr/bin/env python3
"""
Setup script for Metal Sheet AI Inspection System
Checks dependencies and performs initial setup
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def check_gpu():
    """Check CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("⚠️ CUDA not available, will use CPU (slower performance)")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def check_dependencies():
    """Check required dependencies"""
    required_packages = [
        'streamlit',
        'opencv-python', 
        'numpy',
        'torch',
        'transformers',
        'supervision',
        'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
                print(f"✅ {package}: {cv2.__version__}")
            elif package == 'PIL':
                from PIL import Image
                print(f"✅ {package}: {Image.__version__}")
            else:
                module = __import__(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package}: {version}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: Not installed")
    
    return len(missing_packages) == 0

def check_huggingface_auth():
    """Check Hugging Face authentication for SAM-3"""
    try:
        from huggingface_hub import HfFolder
        token = HfFolder.get_token()
        if token:
            print("✅ Hugging Face authentication found")
            return True
        else:
            print("⚠️ Hugging Face authentication not found")
            print("   Run: huggingface-cli login (optional for advanced features)")
            return False
    except ImportError:
        print("⚠️ huggingface-hub not installed")
        return False

def check_sam3_availability():
    """Check if SAM-3 is available in current transformers version"""
    try:
        import sys
        sys.path.append('src')
        from detector import SAM3_AVAILABLE
        if SAM3_AVAILABLE:
            print("✅ SAM-3 available in transformers")
            return True
        else:
            print("⚠️ SAM-3 not yet available in this transformers version")
            print("   System will use fallback detection (contour-based)")
            return False
    except Exception as e:
        print(f"⚠️ Could not check SAM-3 availability: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'data/inputs',
        'data/outputs_ng', 
        'data/outputs_ok',
        'data/logs',
        'models/sam3'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory created: {directory}")

def install_dependencies():
    """Install missing dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Metal Sheet AI Inspection System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check GPU availability
    gpu_available = check_gpu()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check Hugging Face auth
    hf_auth = check_huggingface_auth()
    
    # Check SAM-3 availability
    sam3_available = check_sam3_availability()
    
    # Create directories
    create_directories()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print(f"   Python: ✅")
    print(f"   GPU: {'✅' if gpu_available else '⚠️ CPU only'}")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"   SAM-3: {'✅' if sam3_available else '⚠️ Using fallback detection'}")
    print(f"   Hugging Face: {'✅' if hf_auth else '⚠️ Optional for advanced features'}")
    
    if not deps_ok:
        print("\n📦 Installing missing dependencies...")
        if not install_dependencies():
            print("❌ Setup failed")
            return False
    
    print("\n✅ Setup completed successfully!")
    print("\n🚀 To run the application:")
    print("   streamlit run app.py")
    print("   Or use: ./run.sh")
    
    if not sam3_available:
        print("\n📋 Note: Using fallback detection (contour-based)")
        print("   For SAM-3 features, update transformers when available")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
