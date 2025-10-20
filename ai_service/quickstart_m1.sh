#!/bin/bash

# Quick Start Script for M1 Mac
# This script will set up everything you need to run the AI service

set -e

echo "🍎 AI Service - M1 Mac Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if running on Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo "⚠️  Warning: Not running on Apple Silicon (detected: $ARCH)"
    echo "This script is optimized for M1/M2/M3 Macs"
fi

# Check Python version
echo "📦 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10 or higher:"
    echo "   brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "❌ Python 3.10+ required (found $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install PyTorch with MPS support
echo ""
echo "⚡ Installing PyTorch with Apple Silicon support..."
pip install torch torchvision torchaudio --quiet

# Verify MPS
echo ""
echo "🔍 Checking MPS (Metal Performance Shaders) availability..."
MPS_AVAILABLE=$(python3 -c "import torch; print('true' if torch.backends.mps.is_available() else 'false')")

if [ "$MPS_AVAILABLE" = "true" ]; then
    echo "✅ MPS (Apple Silicon GPU) is available! 🚀"
else
    echo "⚠️  MPS not available - will use CPU"
    echo "   Make sure you're on macOS 12.3+ for GPU acceleration"
fi

# Install other requirements
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Installation complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Starting AI Service..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Device: $(python3 -c "import torch; print('MPS (Apple Silicon GPU)' if torch.backends.mps.is_available() else 'CPU')")"
echo "Port: 8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload