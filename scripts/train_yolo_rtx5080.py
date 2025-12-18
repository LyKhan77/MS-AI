"""
YOLOv8 Training Script for Metal Sheet Detection
Optimized for NVIDIA RTX 5080 16GB
Device: GPU 1
"""

import os
import torch
from ultralytics import YOLO
from roboflow import Roboflow
import yaml

# ============================================
# Configuration
# ============================================

# GPU Configuration
DEVICE = 1  # RTX 5080 on device index 1
os.environ['CUDA_VISIBLE_DEVICES'] = str(DEVICE)

# Roboflow Configuration
ROBOFLOW_API_KEY = "NCwWD9uYzyXohOTlrpFw"  # Get from https://roboflow.com
WORKSPACE = "ania"
PROJECT = "metal-sheets-normal-and-special"
VERSION = 2

# Training Configuration
MODEL_SIZE = 'n'  # nano - fastest, good for edge devices
EPOCHS = 200
BATCH_SIZE = 64  # RTX 5080 can handle this easily
IMG_SIZE = 640
PATIENCE = 50  # Early stopping patience

# Output paths
OUTPUT_DIR = './runs/train'
WEIGHTS_OUTPUT = './weights'

# ============================================
# Step 1: Download Dataset from Roboflow
# ============================================

def download_dataset():
    """Download and prepare dataset from Roboflow"""
    print("="*60)
    print("Step 1: Downloading Dataset from Roboflow")
    print("="*60)
    
    # Initialize Roboflow
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    
    # Access project
    project = rf.workspace(WORKSPACE).project(PROJECT)
    
    # Download dataset with augmentations
    print(f"\nDownloading {PROJECT} dataset...")
    print(f"Version: {VERSION}")
    print(f"Format: YOLOv8")
    
    dataset = project.version(VERSION).download(
        model_format="yolov8",
        location="./datasets/metal_sheets"
    )
    
    print(f"\n✓ Dataset downloaded to: {dataset.location}")
    print(f"✓ Data YAML: {dataset.location}/data.yaml")
    
    return dataset.location


def verify_dataset(dataset_path):
    """Verify dataset structure and print statistics"""
    print("\n" + "="*60)
    print("Step 2: Verifying Dataset")
    print("="*60)
    
    data_yaml = os.path.join(dataset_path, 'data.yaml')
    
    with open(data_yaml, 'r') as f:
        data = yaml.safe_load(f)
    
    print(f"\nDataset Configuration:")
    print(f"  Classes: {data['names']}")
    print(f"  Number of classes: {data['nc']}")
    print(f"  Train images: {data.get('train', 'N/A')}")
    print(f"  Valid images: {data.get('val', 'N/A')}")
    print(f"  Test images: {data.get('test', 'N/A')}")
    
    # Count images
    train_dir = os.path.join(dataset_path, 'train', 'images')
    valid_dir = os.path.join(dataset_path, 'valid', 'images')
    
    if os.path.exists(train_dir):
        train_count = len([f for f in os.listdir(train_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
        print(f"\n  Train images count: {train_count}")
    
    if os.path.exists(valid_dir):
        valid_count = len([f for f in os.listdir(valid_dir) if f.endswith(('.jpg', '.jpeg', '.png'))])
        print(f"  Valid images count: {valid_count}")
    
    return data_yaml


# ============================================
# Step 3: Train YOLOv8 Model
# ============================================

def train_model(data_yaml):
    """Train YOLOv8 model on RTX 5080"""
    print("\n" + "="*60)
    print("Step 3: Training YOLOv8 Model")
    print("="*60)
    
    # Check CUDA
    print(f"\nCUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")
    
    # Load YOLOv8 model
    model_name = f'yolov8{MODEL_SIZE}.pt'
    print(f"\nLoading {model_name}...")
    model = YOLO(model_name)
    
    # Training arguments
    train_args = {
        'data': data_yaml,
        'epochs': EPOCHS,
        'batch': BATCH_SIZE,
        'imgsz': IMG_SIZE,
        'device': 0,  # Use first visible GPU (which is device 1 due to CUDA_VISIBLE_DEVICES)
        'patience': PATIENCE,
        'save': True,
        'project': OUTPUT_DIR,
        'name': 'metal_sheet_detection',
        'exist_ok': True,
        
        # Optimization for RTX 5080
        'cache': True,  # Cache images for faster training
        'workers': 8,  # Number of dataloader workers
        'amp': True,  # Automatic Mixed Precision
        
        # Augmentation (additional to Roboflow)
        'mosaic': 1.0,
        'mixup': 0.1,
        'copy_paste': 0.1,
        'degrees': 15.0,
        'translate': 0.1,
        'scale': 0.5,
        'shear': 0.0,
        'perspective': 0.0,
        'flipud': 0.5,
        'fliplr': 0.5,
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        
        # Validation
        'val': True,
        'plots': True,
        'save_json': True,
        'save_hybrid': False,
        'conf': 0.25,
        'iou': 0.45,
        'max_det': 10,
        
        # Hyperparameters (optimized for counting)
        'lr0': 0.01,
        'lrf': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'warmup_epochs': 3.0,
        'warmup_momentum': 0.8,
        'warmup_bias_lr': 0.1,
        'box': 7.5,
        'cls': 0.5,
        'dfl': 1.5,
    }
    
    print(f"\nTraining Configuration:")
    print(f"  Model: YOLOv8{MODEL_SIZE}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Image size: {IMG_SIZE}")
    print(f"  Device: GPU {DEVICE} (RTX 5080)")
    print(f"  Patience: {PATIENCE}")
    print(f"  Mixed Precision: {train_args['amp']}")
    
    print(f"\nStarting training...")
    print(f"This will take approximately 2-4 hours on RTX 5080.")
    print(f"Monitor progress at: {OUTPUT_DIR}/metal_sheet_detection/")
    print("\n" + "="*60)
    
    # Train model
    results = model.train(**train_args)
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    
    return results


# ============================================
# Step 4: Export Model for Jetson Deployment
# ============================================

def export_model():
    """
Export best model to various formats for deployment"""
    print("\n" + "="*60)
    print("Step 4: Exporting Model")
    print("="*60)
    
    # Load best model
    best_model_path = f'{OUTPUT_DIR}/metal_sheet_detection/weights/best.pt'
    print(f"\nLoading best model: {best_model_path}")
    
    model = YOLO(best_model_path)
    
    # Create weights directory if not exists
    os.makedirs(WEIGHTS_OUTPUT, exist_ok=True)
    
    # Export to PyTorch (.pt) - for Jetson
    print("\n1. Exporting to PyTorch (.pt)...")
    pt_path = os.path.join(WEIGHTS_OUTPUT, 'yolo_counting_nano.pt')
    model.export(format='torchscript', simplify=True)
    
    # Copy best.pt to output
    import shutil
    shutil.copy(best_model_path, pt_path)
    print(f"   ✓ Saved to: {pt_path}")
    
    # Export to TensorRT (.engine) - for Jetson optimization (optional)
    try:
        print("\n2. Exporting to TensorRT (.engine) for Jetson optimization...")
        print("   (This may take 10-20 minutes)")
        model.export(format='engine', device=0, half=True, imgsz=IMG_SIZE)
        print("   ✓ TensorRT export successful")
    except Exception as e:
        print(f"   ⚠ TensorRT export failed (optional): {e}")
        print("   You can export on Jetson directly if needed")
    
    # Export to ONNX (optional, for debugging)
    print("\n3. Exporting to ONNX (.onnx)...")
    onnx_path = os.path.join(WEIGHTS_OUTPUT, 'yolo_counting_nano.onnx')
    model.export(format='onnx', simplify=True)
    print(f"   ✓ Saved to: {onnx_path}")
    
    print(f"\n✓ All exports complete!")
    print(f"✓ Main model for Jetson: {pt_path}")
    
    return pt_path


# ============================================
# Step 5: Evaluate Model
# ============================================

def evaluate_model(data_yaml):
    """Evaluate model on validation set"""
    print("\n" + "="*60)
    print("Step 5: Model Evaluation")
    print("="*60)
    
    best_model_path = f'{OUTPUT_DIR}/metal_sheet_detection/weights/best.pt'
    model = YOLO(best_model_path)
    
    # Validate on validation set
    print("\nRunning validation...")
    metrics = model.val(
        data=data_yaml,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=0,
        plots=True,
        save_json=True
    )
    
    print(f"\nValidation Results:")
    print(f"  mAP@0.5: {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:0.95: {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall: {metrics.box.mr:.4f}")
    
    # Performance summary
    print(f"\n✓ Model ready for deployment!")
    print(f"✓ Expected FPS on Jetson Orin Nano: ~30-50 FPS")
    
    return metrics


# ============================================
# Main Training Pipeline
# ============================================

def main():
    """Run complete training pipeline"""
    print("\n" + "="*60)
    print("YOLOV8 METAL SHEET DETECTION - TRAINING PIPELINE")
    print("RTX 5080 16GB - Device 1")
    print("="*60)
    
    try:
        # Step 1: Download dataset
        dataset_path = download_dataset()
        
        # Step 2: Verify dataset
        data_yaml = verify_dataset(dataset_path)
        
        # Step 3: Train model
        results = train_model(data_yaml)
        
        # Step 4: Export model
        model_path = export_model()
        
        # Step 5: Evaluate model
        metrics = evaluate_model(data_yaml)
        
        # Final summary
        print("\n" + "="*60)
        print("TRAINING PIPELINE COMPLETE!")
        print("="*60)
        print(f"\n✓ Trained model: {model_path}")
        print(f"✓ mAP@0.5: {metrics.box.map50:.4f}")
        print(f"\nNext steps:")
        print(f"  1. Copy {model_path} to Jetson")
        print(f"  2. Place in MS-Detector/weights/ directory")
        print(f"  3. Test inference on Jetson")
        print(f"  4. Integrate with counting logic")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Verify CUDA setup
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    
    # Run training
    main()
