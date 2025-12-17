# Base Image JetPack 6 (L4T R36) with PyTorch & CUDA
# Tag r36.2.0 is stable for R36.4 users
FROM dustynv/l4t-pytorch:r36.2.0

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# 1. Install System Dependencies
# libgl1-mesa-glx needed by OpenCV, git for cloning SAM 2
RUN apt-get update && apt-get install -y \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip
RUN pip3 install --upgrade pip

# 3. Copy and Install Python Requirements
COPY requirements.txt .
# --no-deps on ultralytics to prevent torch overwrite
# Add extra-index-url to ensure we can pull pure python packages like ultralytics if dusty's repo fails
RUN pip3 install --no-cache-dir --extra-index-url https://pypi.org/simple -r requirements.txt

# 4. Install SAM 2 (Segment Anything Model 2) from Source
# Compile manually for Jetson
RUN git clone https://github.com/facebookresearch/segment-anything-2.git && \
    cd segment-anything-2 && \
    pip3 install --no-cache-dir --extra-index-url https://pypi.org/simple -e .

# 5. Copy source code
COPY . .

# 6. Expose port
EXPOSE 8000

# 7. Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
