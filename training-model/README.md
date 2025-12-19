# YOLOv11m Metal Sheet Training

## Requirements

```bash
pip install ultralytics roboflow pyyaml
```

## Training Steps

### 1. Run Training Script

```bash
cd training-model
python train_yolo11m.py
```

### 2. Monitor Training

- Training progress will be displayed in terminal
- TensorBoard logs: `tensorboard --logdir runs/train/metalsheet_yolo11m`
- Plots saved to: `runs/train/metalsheet_yolo11m/`

### 3. Training Parameters

- **Model**: YOLOv11m (medium)
- **Epochs**: 100 (with early stopping patience=20)
- **Image Size**: 640x640
- **Batch Size**: 16 (adjust based on GPU memory)
- **Optimizer**: AdamW
- **Learning Rate**: 0.001 → 0.00001 (cosine decay)

### 4. Dataset Info

- **Source**: Roboflow Metal Sheet v6
- **Classes**: 1 (metalsheet only - filtered from 4 classes)
- **Splits**: train/valid/test
- **Format**: YOLOv11

### 5. Output Files

```
runs/train/metalsheet_yolo11m/
├── weights/
│   ├── best.pt          ← Best model (highest mAP)
│   └── last.pt          ← Last epoch model
├── results.png          ← Training curves
├── confusion_matrix.png
├── val_batch0_pred.jpg  ← Validation predictions
└── ...
```

### 6. Deploy Model

After training completes, the best model will be automatically copied to:

```
backend/yolo11m_metalsheet.pt
```

Update `backend/config.py`:

```python
YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'yolo11m_metalsheet.pt')
```

## GPU Memory Requirements

- **YOLOv11m**: ~6-8GB VRAM (batch=16)
- If OOM error, reduce batch size:
  - RTX 4090 (24GB): batch=32
  - RTX 3080 (10GB): batch=8
  - RTX 3060 (12GB): batch=12

## Training Tips

1. **Monitor overfitting**: Watch val/train loss gap
2. **Early stopping**: Will stop if no improvement for 20 epochs
3. **Augmentation**: Enabled (flip, scale, HSV, mosaic)
4. **Checkpoints**: Saved every 10 epochs

## Validation Metrics

- **mAP50**: Mean Average Precision @ IoU=0.5
- **mAP50-95**: mAP averaged over IoU 0.5-0.95
- **Precision**: TP / (TP + FP)
- **Recall**: TP / (TP + FN)

Target metrics for good model:

- mAP50 > 0.90
- mAP50-95 > 0.70
- Precision > 0.85
- Recall > 0.85

## Troubleshooting

### Issue: OOM (Out of Memory)

**Solution**: Reduce batch size in `train_yolo11m.py`:

```python
batch=8  # or 4
```

### Issue: No 'metalsheet' class found

**Solution**: Check dataset class names, update filter logic

### Issue: Training too slow

**Solution**:

- Reduce image size: `imgsz=416`
- Use smaller model: `yolo11s.pt` or `yolo11n.pt`
- Reduce workers: `workers=4`

### Issue: Poor validation results

**Solution**:

- Increase epochs: `epochs=150`
- Adjust augmentation parameters
- Check dataset quality (labels, images)
