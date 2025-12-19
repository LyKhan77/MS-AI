"""
YOLOv11m Training Script for Metal Sheet Detection
Dataset: Roboflow Metal Sheet (class: metalsheet only)
"""

from roboflow import Roboflow
from ultralytics import YOLO
import yaml
import os
import shutil

# ============================================
# 1. Download Dataset from Roboflow
# ============================================
print("📥 Downloading dataset from Roboflow...")

rf = Roboflow(api_key="NCwWD9uYzyXohOTlrpFw")
project = rf.workspace("main-rdhov").project("metal-sheet")
version = project.version(6)
dataset = version.download("yolov11")

print(f"✅ Dataset downloaded to: {dataset.location}")

# ============================================
# 2. Filter Dataset - Keep Only 'metalsheet' Class
# ============================================
print("\n🔍 Filtering dataset - keeping only 'metalsheet' class...")

# Read original data.yaml
data_yaml_path = os.path.join(dataset.location, 'data.yaml')
with open(data_yaml_path, 'r') as f:
    data_config = yaml.safe_load(f)

print(f"Original classes: {data_config['names']}")

# Find metalsheet class index (case-insensitive)
metalsheet_idx = None
for idx, name in enumerate(data_config['names']):
    if name.lower() == 'metalsheet':
        metalsheet_idx = idx
        break

if metalsheet_idx is None:
    raise ValueError("'metalsheet' class not found in dataset!")

print(f"Metalsheet class index: {metalsheet_idx}")

# Filter labels in train/valid/test folders
def filter_labels(labels_dir, target_class_idx):
    """Remove all labels except target class"""
    if not os.path.exists(labels_dir):
        return
    
    removed_count = 0
    kept_count = 0
    
    for label_file in os.listdir(labels_dir):
        if not label_file.endswith('.txt'):
            continue
        
        label_path = os.path.join(labels_dir, label_file)
        filtered_lines = []
        
        with open(label_path, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) > 0 and int(parts[0]) == target_class_idx:
                    # Change class index to 0 (since we only have 1 class now)
                    filtered_lines.append(f"0 {' '.join(parts[1:])}\n")
        
        # Write back filtered labels
        if filtered_lines:
            with open(label_path, 'w') as f:
                f.writelines(filtered_lines)
            kept_count += 1
        else:
            # Remove label file if no metalsheet detected
            os.remove(label_path)
            # Also remove corresponding image
            for ext in ['.jpg', '.jpeg', '.png']:
                img_name = label_file.replace('.txt', ext)
                img_path = os.path.join(labels_dir.replace('labels', 'images'), img_name)
                if os.path.exists(img_path):
                    os.remove(img_path)
                    break
            removed_count += 1
    
    return kept_count, removed_count

# Filter all splits
print("\nFiltering labels...")
for split in ['train', 'valid', 'test']:
    labels_dir = os.path.join(dataset.location, split, 'labels')
    if os.path.exists(labels_dir):
        kept, removed = filter_labels(labels_dir, metalsheet_idx)
        print(f"  {split}: kept {kept} images, removed {removed} images")

# Update data.yaml with single class
data_config['names'] = ['metalsheet']
data_config['nc'] = 1

with open(data_yaml_path, 'w') as f:
    yaml.dump(data_config, f)

print(f"\n✅ Updated data.yaml with single class: {data_config['names']}")


# ============================================
# 3. Train YOLOv11m Model
# ============================================
print("\n🚀 Starting YOLOv11m training...")

# Initialize model
model = YOLO('yolo11m.pt')  # YOLOv11m pretrained

# Train
results = model.train(
    data=data_yaml_path,
    epochs=100,              # Adjust based on your needs
    imgsz=640,               # Image size
    batch=16,                # Batch size (adjust based on GPU memory)
    device=0,                # GPU device (0 for first GPU, 'cpu' for CPU)
    workers=8,               # Number of workers
    project='runs/train',    # Save location
    name='metalsheet_yolo11m',
    patience=20,             # Early stopping patience
    save=True,
    save_period=10,          # Save checkpoint every 10 epochs
    
    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=10.0,
    translate=0.1,
    scale=0.5,
    shear=0.0,
    perspective=0.0,
    flipud=0.0,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.0,
    
    # Optimization
    optimizer='AdamW',
    lr0=0.001,
    lrf=0.01,
    momentum=0.937,
    weight_decay=0.0005,
    warmup_epochs=3.0,
    warmup_momentum=0.8,
    warmup_bias_lr=0.1,
    
    # Loss
    box=7.5,
    cls=0.5,
    dfl=1.5,
    
    # Validation
    val=True,
    plots=True,
    verbose=True
)

print("\n✅ Training completed!")
print(f"📊 Results saved to: runs/train/metalsheet_yolo11m")
print(f"🎯 Best model: runs/train/metalsheet_yolo11m/weights/best.pt")

# ============================================
# 4. Validate Model
# ============================================
print("\n🔍 Validating model...")

best_model = YOLO('runs/train/metalsheet_yolo11m/weights/best.pt')
metrics = best_model.val()

print(f"\n📈 Validation Metrics:")
print(f"  mAP50: {metrics.box.map50:.4f}")
print(f"  mAP50-95: {metrics.box.map:.4f}")
print(f"  Precision: {metrics.box.mp:.4f}")
print(f"  Recall: {metrics.box.mr:.4f}")

# ============================================
# 5. Export Model for Deployment
# ============================================
print("\n📦 Copying best model to backend...")

best_model_path = 'runs/train/metalsheet_yolo11m/weights/best.pt'
target_path = '../backend/yolo11m_metalsheet.pt'

shutil.copy(best_model_path, target_path)
print(f"✅ Model copied to: {target_path}")

print("\n🎉 Training pipeline completed successfully!")
print("\nNext steps:")
print("1. Update backend/config.py: YOLO_MODEL_PATH = 'yolo11m_metalsheet.pt'")
print("2. Restart backend server")
print("3. Test detection with your video")
