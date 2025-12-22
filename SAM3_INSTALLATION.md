# SAM-3 Installation Guide

## Quick Start (Mock Mode - Testing)

Your system is already configured for **mock mode** testing. No SAM-3 installation needed!

```bash
# Backend already works in mock mode
cd backend
python app.py

# Frontend
cd frontend
npm run dev
```

Test the Defects page - it will generate random defects for demonstration.

---

## Production Setup (Real SAM-3 Model)

### Step 1: Install Dependencies

```bash
cd backend
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118  # For CUDA 11.8
```

### Step 2: Install SAM-3

**Option A: Official SAM-3 Package (if available)**

```bash
pip install sam3
```

**Option B: Segment Anything (SAM 2 - Fallback)**

```bash
pip install segment-anything
```

### Step 3: Download Model Checkpoint

```bash
mkdir -p models
cd models

# Download SAM-3 checkpoint (~2.4GB)
# URL depends on your SAM-3 source
# If using your reference project, copy the checkpoint:
cp /path/to/SAM3-project_reference/checkpoint.pth ./sam3_vit_h.pth
```

### Step 4: Test Model Loading

```bash
cd backend
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"
```

**Expected Output:**

```
[DefectAnalyzer] Initialized on device: cuda
[DefectAnalyzer] Loading SAM-3 from models/sam3_vit_h.pth...
[DefectAnalyzer] SAM-3 loaded successfully!
[DefectAnalyzer] Model on device: cuda:0
```

---

## Configuration

### Custom Model Path

Edit `backend/core/defect_analyzer.py`:

```python
# Default
DefectAnalyzer(checkpoint_path='models/sam3_vit_h.pth')

# Custom
DefectAnalyzer(checkpoint_path='/path/to/your/checkpoint.pth')
```

### Adjust Detection Parameters

```python
# In defect_analyzer.py __init__:

# Confidence threshold (0-1)
self.confidence_threshold = 0.5  # Lower = more detections

# Severity thresholds (pixels²)
self.severity_thresholds = {
    'minor': 100,
    'moderate': 500,
    'critical': 9999999
}
```

### Custom Defect Types

```python
# In defect_analyzer.py __init__:
self.defect_prompts = {
    'scratch': 'linear scratch mark on metal surface',
    'dent': 'dent or deformation on metal sheet',
    'rust': 'rust spot or corrosion on metal',
    'hole': 'hole or perforation in metal',
    'coating_bubble': 'paint bubble or coating defect',
    # Add your custom defects:
    'crack': 'crack line on metal surface',
    'discoloration': 'color stain or discoloration'
}
```

---

## Troubleshooting

### Issue: "Module 'sam3' not found"

Fallback to SAM 2:

```bash
pip install git+https://github.com/facebookresearch/segment-anything.git
```

### Issue: CUDA out of memory

Reduce batch processing or switch to CPU:

```python
DefectAnalyzer(device='cpu')
```

### Issue: Text prompts not working

The system will skip unsupported defect types and print:

```
[DefectAnalyzer] Text prompts not supported, skipping scratch
```

Ensure you're using SAM-3 (not SAM 2) for text-based prompting.

---

## Performance Expectations

| Mode            | Processing Speed    | Accuracy           |
| --------------- | ------------------- | ------------------ |
| **Mock**        | ~1-2s for 10 images | Random (demo only) |
| **SAM-3 (GPU)** | ~10-30s per image   | High (zero-shot)   |
| **SAM-3 (CPU)** | ~60-120s per image  | High (zero-shot)   |

---

## Next Steps

1. ✅ Test in mock mode first
2. ✅ Install SAM-3 dependencies
3. ✅ Download checkpoint
4. ✅ Test on real images
5. ✅ Tune thresholds
6. ✅ (Optional) Fine-tune model
