#!/bin/bash

# AI Service Startup Script
# Sets up environment and starts the FastAPI service

set -e

echo "🚀 Starting AI Deepfake Detection Service..."

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | grep -Po '(?<=Python )(.+)')
echo "📦 Python version: $PYTHON_VERSION"

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
else
    echo "💻 No GPU detected, using CPU"
    export CUDA_VISIBLE_DEVICES=""
fi

# Load environment variables
if [ -f .env ]; then
    echo "📝 Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set defaults
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-1}
export WEIGHTS_DIR=${WEIGHTS_DIR:-$(pwd)/weights}

# Model weights (~4 GB) download into $WEIGHTS_DIR on first start
mkdir -p "$WEIGHTS_DIR"

# Run database migrations (if applicable)
# python -m alembic upgrade head

# Start the service
echo "🌐 Starting server on $HOST:$PORT with $WORKERS workers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info \
    --access-log \
    --loop asyncio