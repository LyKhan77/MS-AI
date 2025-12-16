#!/usr/bin/env python3

# Test script for checking imports
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    print("🔧 Testing imports for Metal Sheet AI Inspection System...")
    print("=" * 60)
    
    # Test basic Python packages
    try:
        import streamlit as st
        print(f"✅ Streamlit: {st.__version__}")
    except Exception as e:
        print(f"❌ Streamlit: {e}")
    
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except Exception as e:
        print(f"❌ OpenCV: {e}")
    
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except Exception as e:
        print(f"❌ NumPy: {e}")
    
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        print(f"   CUDA available: {torch.cuda.is_available()}")
    except Exception as e:
        print(f"❌ PyTorch: {e}")
    
    try:
        import transformers
        print(f"✅ Transformers: {transformers.__version__}")
    except Exception as e:
        print(f"❌ Transformers: {e}")
    
    try:
        import supervision as sv
        print(f"✅ Supervision: {sv.__version__}")
    except Exception as e:
        print(f"❌ Supervision: {e}")
    
    # Test our custom modules
    print("\n📦 Testing custom modules...")
    
    try:
        from detector import SAM3Engine, SAM3_AVAILABLE
        print(f"✅ Detector module imported successfully")
        print(f"   SAM-3 Available: {SAM3_AVAILABLE}")
        
        # Test basic initialization
        engine = SAM3Engine()
        print(f"   SAM3Engine initialized successfully")
        print(f"   Using fallback: {engine.use_fallback}")
        
    except Exception as e:
        print(f"❌ Detector module error: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        from camera import VideoStreamer, MotionDetector, InputSource
        print("✅ Camera module imported successfully")
    except Exception as e:
        print(f"❌ Camera module error: {e}")
    
    try:
        from processing import ImageProcessor
        print("✅ Processing module imported successfully")
    except Exception as e:
        print(f"❌ Processing module error: {e}")
    
    try:
        from ui_components import render_sidebar_config
        print("✅ UI components module imported successfully")
    except Exception as e:
        print(f"❌ UI components module error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Import test completed!")

if __name__ == "__main__":
    test_imports()
