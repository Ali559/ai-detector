> **Outdated:** this guide predates detection v1. Endpoints, model and environment variables have changed; see [README.md](README.md).

# 🍎 M1 Mac - Quick Reference

## TL;DR - Get Started in 2 Minutes

```bash
# 1. Make the script executable and run it
chmod +x quickstart_m1.sh
./quickstart_m1.sh

# That's it! The service will start automatically.
```

## What Changed for M1?

### ✅ What Works

- **Apple Silicon GPU (MPS)** - Automatic detection and usage
- **All features** - Same functionality as NVIDIA version
- **Better performance** - Optimized for Metal Performance Shaders

### ❌ What Doesn't Work

- **Docker GPU passthrough** - Docker can't access M1 GPU
- **CUDA operations** - M1 uses MPS instead
- **FP16 on MPS** - Not yet supported (but still fast!)

## Key Code Changes

### 1. Device Detection (Already Updated)

```python
# Automatically detects MPS
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"  # ← M1 GPU
else:
    device = "cpu"
```

### 2. Dependencies (Already Updated)

```txt
# requirements.txt uses standard PyTorch
torch>=2.0.0  # MPS support included
torchvision>=0.15.0
```

## Installation Methods

### Method 1: One-Line Setup (Easiest)

```bash
chmod +x quickstart_m1.sh && ./quickstart_m1.sh
```

### Method 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install PyTorch
pip install torch torchvision torchaudio

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload
```

### Method 3: Using Makefile

```bash
make install  # Install everything
make dev      # Run development server
```

## Verify GPU Usage

```bash
# Check if MPS is available
python3 -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"

# Check health endpoint
curl http://localhost:8000/health
# Should show: "gpu_available": true
```

## Performance Comparison

| Device          | Single Image | Batch (8) |
| --------------- | ------------ | --------- |
| M1 Pro          | ~100-150ms   | ~400ms    |
| M1 Max          | ~70-100ms    | ~300ms    |
| M2/M3 Pro       | ~70-100ms    | ~300ms    |
| NVIDIA RTX 3080 | ~50ms        | ~150ms    |

**Note**: M1 is still very fast! Only 2-3x slower than high-end NVIDIA cards.

## Common Issues & Fixes

### "MPS not available"

```bash
# Check macOS version (needs 12.3+)
sw_vers

# Reinstall PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio
```

### "Out of memory"

```bash
# Close Chrome and other GPU apps
# Or reduce batch size in code
```

### "Slow performance"

```bash
# Check GPU usage
pip install asitop
sudo asitop

# Make sure other apps aren't using GPU
```

## Environment Variables

Create `.env`:

```bash
MODEL_PATH=./models/deepfake_detector.pth
EMBEDDING_DIM=768
DETECTION_THRESHOLD=0.7
HOST=0.0.0.0
PORT=8000
```

## Docker on M1

**Don't use Docker for GPU tasks on M1.** Docker Desktop on Mac cannot access the GPU.

If you must use Docker (CPU only):

```bash
docker build -f Dockerfile.m1 -t ai-service-m1 .
docker run -p 8000:8000 ai-service-m1
```

But seriously, **just run it natively** for 5-10x better performance.

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Test analysis
curl -X POST http://localhost:8000/analyze \
  -F "file=@test.jpg"

# Run test suite
make test
```

## Integration with Node.js

Your Node.js service connects the same way:

```javascript
// From Node.js
const response = await axios.post("http://localhost:8000/analyze", formData);
```

No changes needed on the Node.js side!

## Pro Tips

1. **Keep the service running** - Model loads once and stays in memory
2. **Use batch endpoint** - More efficient for multiple images
3. **Monitor temperature** - M1 can throttle under sustained load
4. **Close Chrome** - Frees up GPU memory
5. **First run is slow** - Model downloads (~90MB)

## Need More Help?

- Full guide: See `SETUP_M1.md`
- Troubleshooting: Check the troubleshooting section
- Performance: Read the performance optimization guide

---

**Bottom line**: Everything works great on M1! Just skip Docker and run natively.
