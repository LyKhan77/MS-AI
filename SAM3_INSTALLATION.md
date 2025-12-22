# SAM-3 Installation Guide (HuggingFace Transformers)

## Quick Setup for HuggingFace SAM-3

Your reference project uses **SAM-3 from HuggingFace Transformers**, not the standalone SAM-3 package.

### Step 1: Install Dependencies on PC GPU

```bash
# SSH to PC GPU
ssh gspe-ai3@gspe-ai3-MS-7E32

# Navigate to project
cd /home/gspe-ai3/project_cv/MS-AI/backend

# Activate virtual environment
source venv/bin/activate

# Install HuggingFace Transformers (from main branch for latest SAM-3)
pip install git+https://github.com/huggingface/transformers

# Or install stable version:
# pip install transformers

# Install other required packages
pip install torch torchvision opencv-python pillow
```

### Step 2: Test Model Loading

```bash
# Test SAM-3 model loads correctly
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"
```

**Expected Output:**

```
[DefectAnalyzer] Initialized on device: cuda
[DefectAnalyzer] Loading SAM-3 from HuggingFace Transformers...
[DefectAnalyzer] Loading model: facebook/sam3-large
Downloading model files...
[DefectAnalyzer] SAM-3 loaded successfully from HuggingFace!
[DefectAnalyzer] Model on device: cuda:0
```

**First Run Note:** Model will be downloaded from HuggingFace (~1-2GB). Subsequent runs will use cached model.

---

## How It Works

### HuggingFace SAM-3 Approach

```python
from transformers import AutoProcessor, AutoModelForMaskGeneration

# Load model from HuggingFace Hub
processor = AutoProcessor.from_pretrained("facebook/sam3-large")
model = AutoModelForMaskGeneration.from_pretrained("facebook/sam3-large")

# Prepare inputs with text prompt
inputs = processor(
    images=pil_image,
    text=["scratch on metal surface"],  # Zero-shot text prompt
    return_tensors="pt"
)

# Run inference
outputs = model(**inputs)

# Get masks and scores
masks = outputs.pred_masks
scores = outputs.iou_scores
```

### Zero-Shot Defect Detection

The system uses text prompts to detect defects **without training**:

```python
defect_prompts = {
    'scratch': 'linear scratch mark on metal surface',
    'dent': 'dent or deformation on metal sheet',
    'rust': 'rust spot or corrosion on metal',
    'hole': 'hole or perforation in metal',
    'coating_bubble': 'paint bubble or coating defect'
}
```

---

## Model Options

### Available SAM-3 Models

| Model ID              | Size   | Accuracy | Speed     |
| --------------------- | ------ | -------- | --------- |
| `facebook/sam3-large` | ~1.2GB | Good     | Fast      |
| `facebook/sam3-huge`  | ~2.4GB | Better   | Slower    |
| `facebook/sam3-base`  | ~350MB | OK       | Very Fast |

### Change Model (Optional)

Edit `backend/core/defect_analyzer.py`:

```python
# Line ~75 in load_model()
model_id = "facebook/sam3-large"  # Change to sam3-huge or sam3-base
```

---

## Configuration

### Adjust Detection Parameters

`backend/core/defect_analyzer.py`:

```python
# Confidence threshold (0-1)
self.confidence_threshold = 0.5  # Lower = more detections

# Severity thresholds (pixels²)
self.severity_thresholds = {
    'minor': 100,      # Small defects
    'moderate': 500,   # Medium defects
    'critical': 9999999  # Large defects
}
```

### Custom Defect Types

Add your own defect prompts:

```python
self.defect_prompts = {
    'scratch': 'linear scratch mark on metal surface',
    'dent': 'dent or deformation on metal sheet',
    'rust': 'rust spot or corrosion on metal',
    'hole': 'hole or perforation in metal',
    'coating_bubble': 'paint bubble or coating defect',
    # Add custom:
    'crack': 'crack or fracture line on metal',
    'weld_defect': 'poor weld or welding defect'
}
```

---

## Troubleshooting

### Issue: "No module named 'transformers'"

```bash
pip install git+https://github.com/huggingface/transformers
```

### Issue: Model download fails

Check internet connection and HuggingFace Hub access:

```bash
python -c "from transformers import AutoProcessor; AutoProcessor.from_pretrained('facebook/sam3-large')"
```

### Issue: CUDA out of memory

Use smaller model or CPU:

```python
# In defect_analyzer.py __init__():
DefectAnalyzer(device='cpu')  # Use CPU instead

# Or use smaller model:
model_id = "facebook/sam3-base"  # Smaller model
```

### Issue: Mock mode still active

Check for errors in model loading:

```bash
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"
```

If you see `Falling back to mock mode`, check the error message above it.

---

## Complete Setup Commands (Copy-Paste Ready)

```bash
# On PC GPU via SSH
cd /home/gspe-ai3/project_cv/MS-AI/backend
source venv/bin/activate

# Install transformers from main branch (for latest SAM-3)
pip install git+https://github.com/huggingface/transformers

# Test
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"

# If successful, restart backend
cd ..
python app.py
```

---

## Performance Expectations

| Mode            | Processing Speed    | Accuracy           |
| --------------- | ------------------- | ------------------ |
| **Mock**        | ~1-2s for 10 images | Random (demo only) |
| **SAM-3 (GPU)** | ~5-15s per image    | High (zero-shot)   |
| **SAM-3 (CPU)** | ~30-60s per image   | High (zero-shot)   |

**Note:** First image takes longer due to model initialization. Subsequent images are faster.

---

## Next Steps

1. ✅ Install transformers on PC GPU
2. ✅ Test model loading
3. ✅ Run backend (`python app.py`)
4. ✅ Test defect detection on Defects page
5. ✅ Tune confidence thresholds if needed
