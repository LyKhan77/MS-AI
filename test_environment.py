"""
Environment verification script for Jetson Orin Nano
Tests all required dependencies and hardware capabilities
"""

import sys
import platform

def print_section(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_python():
    """Test Python version"""
    print_section("Python Environment")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    
    major, minor = sys.version_info[:2]
    if major == 3 and minor >= 10:
        print("✓ Python version is compatible (>= 3.10)")
        return True
    else:
        print("✗ Python version too old. Requires >= 3.10")
        return False

def test_pytorch():
    """Test PyTorch and CUDA"""
    print_section("PyTorch & CUDA")
    try:
        import torch
        print(f"✓ PyTorch imported successfully")
        print(f"  Version: {torch.__version__}")
        
        # CUDA availability
        cuda_available = torch.cuda.is_available()
        print(f"  CUDA available: {cuda_available}")
        
        if cuda_available:
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  cuDNN version: {torch.backends.cudnn.version()}")
            print(f"  Number of GPUs: {torch.cuda.device_count()}")
            
            if torch.cuda.device_count() > 0:
                print(f"  GPU 0: {torch.cuda.get_device_name(0)}")
                
                # Memory info
                total_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                print(f"  Total GPU memory: {total_mem:.2f} GB")
                
                # Test tensor operation
                try:
                    test_tensor = torch.randn(100, 100).cuda()
                    result = torch.matmul(test_tensor, test_tensor)
                    print("✓ GPU tensor operations working")
                    return True
                except Exception as e:
                    print(f"✗ GPU tensor operation failed: {e}")
                    return False
        else:
            print("✗ CUDA not available - will run on CPU only")
            return False
            
    except ImportError as e:
        print(f"✗ PyTorch not installed: {e}")
        return False

def test_opencv():
    """Test OpenCV"""
    print_section("OpenCV")
    try:
        import cv2
        print("✓ OpenCV imported successfully")
        print(f"  Version: {cv2.__version__}")
        
        # Test CUDA support in OpenCV (optional)
        cuda_enabled = cv2.cuda.getCudaEnabledDeviceCount() > 0
        if cuda_enabled:
            print(f"  OpenCV CUDA support: Enabled")
        else:
            print(f"  OpenCV CUDA support: Disabled (optional)")
        
        return True
    except ImportError as e:
        print(f"✗ OpenCV not installed: {e}")
        return False

def test_ultralytics():
    """Test Ultralytics (YOLO)"""
    print_section("Ultralytics (YOLO)")
    try:
        from ultralytics import YOLO
        import ultralytics
        print("✓ Ultralytics imported successfully")
        print(f"  Version: {ultralytics.__version__}")
        
        # Test if YOLO can be instantiated (will download model if needed)
        try:
            model = YOLO('yolov8n.pt')  # Nano model
            print("✓ YOLO model loaded successfully")
            return True
        except Exception as e:
            print(f"⚠ YOLO model initialization warning: {e}")
            print("  (This is normal if model weights are not yet downloaded)")
            return True
            
    except ImportError as e:
        print(f"✗ Ultralytics not installed: {e}")
        return False

def test_flask():
    """Test Flask"""
    print_section("Flask Web Framework")
    try:
        import flask
        print("✓ Flask imported successfully")
        print(f"  Version: {flask.__version__}")
        return True
    except ImportError as e:
        print(f"✗ Flask not installed: {e}")
        return False

def test_other_dependencies():
    """Test other required packages"""
    print_section("Other Dependencies")
    
    packages = {
        'PIL': 'Pillow',
        'numpy': 'NumPy',
        'requests': 'Requests',
        'pydantic': 'Pydantic',
        'dotenv': 'python-dotenv',
    }
    
    all_ok = True
    for module, name in packages.items():
        try:
            if module == 'dotenv':
                __import__('dotenv')
            else:
                __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} not installed")
            all_ok = False
    
    return all_ok

def test_sam2():
    """Test SAM2 (Segment Anything Model 2)"""
    print_section("SAM2 (Segment Anything Model 2)")
    try:
        # Try to import SAM2
        import sam2
        print("✓ SAM2 imported successfully")
        
        # Check if checkpoint exists
        from pathlib import Path
        checkpoint_path = Path('./weights/sam2_hiera_tiny.pt')
        if checkpoint_path.exists():
            print(f"✓ SAM2 checkpoint found at {checkpoint_path}")
        else:
            print(f"⚠ SAM2 checkpoint not found at {checkpoint_path}")
            print("  Download it with:")
            print("  wget https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_tiny.pt -P weights/")
        
        return True
    except ImportError as e:
        print(f"⚠ SAM2 not installed (will be needed for Phase 2): {e}")
        return True  # Not critical for Phase 1

def test_system_info():
    """Display system information"""
    print_section("System Information")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    
    # Try to read Jetson info
    try:
        with open('/etc/nv_tegra_release', 'r') as f:
            jetson_info = f.read()
            print(f"\nJetson Info:")
            for line in jetson_info.strip().split('\n'):
                if line and not line.startswith('#'):
                    print(f"  {line}")
    except FileNotFoundError:
        print("⚠ Not running on Jetson device")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  METAL SHEET QC DETECTION SYSTEM")
    print("  Environment Verification")
    print("="*60)
    
    test_system_info()
    
    results = {
        'Python': test_python(),
        'PyTorch & CUDA': test_pytorch(),
        'OpenCV': test_opencv(),
        'Ultralytics': test_ultralytics(),
        'Flask': test_flask(),
        'Other Dependencies': test_other_dependencies(),
        'SAM2': test_sam2(),
    }
    
    # Summary
    print_section("Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} components verified")
    
    if passed == total:
        print("\n✓ All components verified successfully!")
        print("✓ System is ready for development")
        return 0
    else:
        print(f"\n⚠ {total - passed} component(s) failed verification")
        print("Please install missing dependencies")
        return 1

if __name__ == "__main__":
    sys.exit(main())
