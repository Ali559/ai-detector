> **Outdated:** this guide predates detection v1. Endpoints, model and environment variables have changed; see [README.md](README.md).

# 🍎 M1 Mac Setup Guide

Special instructions for running the AI service on Apple Silicon (M1/M2/M3) Macs.

## 🎯 Key Differences

- **No CUDA**: Apple Silicon uses Metal Performance Shaders (MPS) instead of NVIDIA CUDA
- **No Docker GPU**: Docker Desktop on Mac doesn't support GPU passthrough
- **Native Performance**: Run locally for best performance on M1

## 📦 Prerequisites

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.10 or 3.11
brew install python@3.11
```

## 🚀 Installation Steps

### 1. Create Virtual Environment

```bash
cd ai-service

# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate
```

### 2. Install PyTorch with MPS Support

```bash
# Install PyTorch optimized for Apple Silicon
pip install torch torchvision torchaudio
```

### 3. Install Dependencies

```bash
# Install all other requirements
pip install -r requirements.txt
```

### 4. Verify MPS is Available

```bash
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

Expected output: `MPS available: True`

## 🏃 Running the Service

### Option 1: Direct Run (Recommended for M1)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Using the Makefile

```bash
make install  # Install dependencies
make dev      # Run development server
```

### Option 3: Production Mode

```bash
# Create .env file
cp .env.example .env

# Edit .env if needed
nano .env

# Run with start script
chmod +x start.sh
./start.sh
```

## 🧪 Testing

```bash
# Test health check
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "model_loaded": true,
#   "gpu_available": true  # This means MPS is being used!
# }

# Test with an image
curl -X POST "http://localhost:8000/analyze" \
  -F "file=@test_image.jpg" \
  | python -m json.tool
```

## ⚡ Performance on M1

### M1 Pro Benchmarks

- **Single image**: ~100-150ms
- **Batch (8 images)**: ~400-500ms
- **Memory usage**: ~2GB

### M1 Max/M2/M3 Pro

- **Single image**: ~70-100ms
- **Batch (8 images)**: ~300-400ms

### Tips for Better Performance

1. **Use batch processing** when analyzing multiple images
2. **Keep model loaded** (it stays in memory between requests)
3. **Close other GPU-intensive apps** (Chrome with many tabs, etc.)

## 🐳 Docker on M1 (CPU Only)

Docker Desktop on M1 Mac **cannot** access the GPU. You have two options:

### Option 1: CPU-only Docker (Not Recommended)

```dockerfile
# Use ARM64 compatible base image
FROM python:3.11-slim-bullseye

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install torch torchvision torchaudio

# Copy app
COPY ./app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Option 2: Run Natively (Recommended)

Skip Docker entirely and run the service directly on your Mac for GPU acceleration.

## 🔧 Troubleshooting

### Issue: "MPS backend out of memory"

```bash
# Reduce batch size or image dimensions
# Edit app/services/image_processing.py
# Change target_size from (224, 224) to (192, 192)
```

### Issue: "torch.backends.mps.is_available() returns False"

```bash
# Reinstall PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio

# Check macOS version (requires macOS 12.3+)
sw_vers
```

### Issue: Slow performance

```bash
# Check if other processes are using GPU
sudo powermetrics --samplers gpu_power -i 1000 -n 1

# Close GPU-intensive applications
# Chrome, Final Cut Pro, etc.
```

## 📊 Monitoring GPU Usage

```bash
# Install asitop for M1 GPU monitoring
pip install asitop

# Run in another terminal
sudo asitop
```

## 🔄 Switching Between CPU and MPS

The service automatically detects and uses the best available device:

```bash
# Force CPU mode (for testing)
export PYTORCH_ENABLE_MPS_FALLBACK=1
python -c "import torch; print(torch.device('cpu'))"

# Use MPS (default)
unset PYTORCH_ENABLE_MPS_FALLBACK
```

## 📝 Environment Variables for M1

Create a `.env` file:

```bash
# Model configuration
MODEL_PATH=./models/deepfake_detector.pth
EMBEDDING_DIM=768
DETECTION_THRESHOLD=0.7

# Server configuration
HOST=0.0.0.0
PORT=8000
WORKERS=1

# M1 specific
PYTORCH_ENABLE_MPS_FALLBACK=0
```

## 🎓 Additional Resources

- [PyTorch MPS Backend](https://pytorch.org/docs/stable/notes/mps.html)
- [Apple Silicon Performance](https://developer.apple.com/metal/pytorch/)
- [Optimizing ML on M1](https://huggingface.co/docs/transformers/perf_train_gpu_one)

## ✅ Quick Verification Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] PyTorch installed with MPS support
- [ ] All requirements installed
- [ ] MPS availability confirmed
- [ ] Service starts without errors
- [ ] Health check returns `gpu_available: true`
- [ ] Test image analysis works

## 💡 Pro Tips

1. **First run is slow**: Model downloads on first use (~90MB)
2. **Keep service running**: Restarting loses the loaded model in memory
3. **Use HTTP/2**: For better performance with Node.js integration
4. **Monitor temperature**: M1 chips can throttle under sustained load

---

**Need help?** The service should work out of the box on M1 Macs. If you encounter issues, check the troubleshooting section above.
