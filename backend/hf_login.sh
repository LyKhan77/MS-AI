#!/bin/bash
# HuggingFace Login Script untuk SAM-3
# Run di: /home/gspe-ai3/project_cv/MS-AI/backend

echo "🔐 HuggingFace Authentication Setup"
echo "===================================="
echo ""

# Activate venv
source venv/bin/activate

# Check if huggingface-cli is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "📦 Installing huggingface-hub..."
    pip install huggingface-hub
fi

echo "🌐 Get your token from: https://huggingface.co/settings/tokens"
echo ""
echo "📝 Click 'Create new token' if you don't have one"
echo "   - Name: SAM3-Project"  
echo "   - Type: Read"
echo ""
echo "Then paste your token below:"
echo ""

# Login
huggingface-cli login

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Login successful!"
    echo ""
    echo "🧪 Testing SAM-3 access..."
    python -c "
from transformers import AutoImageProcessor, AutoModel
try:
    print('📥 Downloading SAM-3 model (first time only, ~2GB)...')
    processor = AutoImageProcessor.from_pretrained('facebook/sam3')
    model = AutoModel.from_pretrained('facebook/sam3')
    print('✅ SAM-3 model loaded successfully!')
except Exception as e:
    print(f'❌ Error: {e}')
"
else
    echo "❌ Login failed"
fi
