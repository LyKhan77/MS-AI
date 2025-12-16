#!/bin/bash

# Metal Sheet AI Inspection System - Quick Start Script

echo "🔧 Metal Sheet AI Inspection System"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3.10 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
python setup.py

# Check for Hugging Face authentication
echo "Checking Hugging Face authentication..."
if ! huggingface-cli whoami &>/dev/null; then
    echo "Please login to Hugging Face to access SAM-3 model:"
    echo "huggingface-cli login"
    read -p "Press Enter after logging in..."
fi

# Run the application
echo "Starting Metal Sheet AI Inspection System..."
echo "Application will be available at: http://localhost:8501"
streamlit run app.py
