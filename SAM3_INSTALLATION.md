# SAM-3 Setup & Testing Guide

## Quick Start

### Step 1: Login to HuggingFace

**Option 1 - Using Script (Easiest):**

```bash
cd /home/gspe-ai3/project_cv/MS-AI/backend
source venv/bin/activate
chmod +x hf_login.sh
./hf_login.sh
```

**Option 2 - Manual:**

```bash
cd /home/gspe-ai3/project_cv/MS-AI/backend
source venv/bin/activate
pip install huggingface-hub
huggingface-cli login
# Paste your token from: https://huggingface.co/settings/tokens
```

### Step 2: Test SAM-3 Loading

```bash
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"
```

**Expected:**

```
[DefectAnalyzer] Initialized on device: cuda
[DefectAnalyzer] Loading SAM-3 from HuggingFace Transformers...
[DefectAnalyzer] Loading model: facebook/sam3
Downloading model... (first time only, ~2GB)
[DefectAnalyzer] SAM-3 loaded successfully from HuggingFace!
[DefectAnalyzer] Model on device: cuda:0
```

### Step 3: Start Backend

```bash
cd /home/gspe-ai3/project_cv/MS-AI
python backend/app.py
```

---

## Complete Installation

```bash
# On PC GPU (via SSH)
cd /home/gspe-ai3/project_cv/MS-AI/backend
source venv/bin/activate

# Install dependencies
pip install transformers huggingface-hub torch torchvision pillow opencv-python

# Login to HuggingFace
./hf_login.sh

# Test
python -c "from core.defect_analyzer import DefectAnalyzer; analyzer = DefectAnalyzer(); analyzer.load_model()"
```

---

## How It Works

### 1. Model Loading

```python
from transformers import AutoImageProcessor, AutoModel

processor = AutoImageProcessor.from_pretrained("facebook/sam3")
model = AutoModel.from_pretrained("facebook/sam3")
```

### 2. Inference (Text-Prompted)

```python
# Prepare inputs
inputs = processor(
    images=pil_image,
    text=["scratch on metal surface"],
    return_tensors="pt"
)

# Run inference
outputs = model(**inputs)

# Get masks
masks = outputs.pred_masks  # or outputs['masks']
scores = outputs.iou_scores  # or outputs['scores']
```

---

## Troubleshooting

### "401 Unauthorized" or "Repository Not Found"

**Solution:** Login to HuggingFace

```bash
huggingface-cli login
```

### "No module named 'transformers'"

```bash
pip install transformers
```

### Still falling back to mock mode

Check error message in console. Common issues:

- Not logged in → Run `huggingface-cli login`
- Wrong model ID → Should be `facebook/sam3`
- No internet connection → Check connection

---

## Model Information

- **Model ID:** `facebook/sam3`
- **Size:** ~2.4GB
- **Cache Location:** `~/.cache/huggingface/hub/`
- **Requirements:** HuggingFace account + Read token

---

## Testing Workflow

1. **Login:** `./hf_login.sh`
2. **Test Load:** `python -c "from core.defect_analyzer import get_defect_analyzer; analyzer = get_defect_analyzer(); analyzer.load_model()"`
3. **Run Backend:** `python app.py`
4. **Test Frontend:** Open Defects page, select session, click "Run Segmentation"

---

## Performance

| Mode        | Speed               | Accuracy              |
| ----------- | ------------------- | --------------------- |
| Mock        | ~1-2s for 10 images | Random (testing only) |
| SAM-3 (GPU) | ~10-20s per image   | High (zero-shot)      |
| SAM-3 (CPU) | ~60-120s per image  | High (zero-shot)      |
