# ☁️ Cloud GPU Deployment Guide

Since you can't run NVIDIA CUDA on M1 Mac, here are cloud options for GPU acceleration.

## 🚀 Quick Comparison

| Service              | GPU      | Cost/Hour   | Setup Time | Best For    |
| -------------------- | -------- | ----------- | ---------- | ----------- |
| **RunPod**           | RTX 4090 | $0.34       | 2 min      | Development |
| **Vast.ai**          | RTX 3090 | $0.20       | 5 min      | Budget      |
| **Lambda Labs**      | A100     | $1.10       | 5 min      | Production  |
| **Google Colab Pro** | T4       | $10/mo      | 1 min      | Testing     |
| **AWS EC2 (g4dn)**   | T4       | $0.526      | 15 min     | Production  |
| **Modal**            | A100     | Pay-per-use | 10 min     | Serverless  |

## 1️⃣ RunPod (Easiest & Cheapest)

**Best for development and testing**

### Setup (2 minutes)

```bash
# 1. Sign up at runpod.io
# 2. Deploy a pod with PyTorch template
# 3. Upload your code via Jupyter or SSH
# 4. Run the service
```

### Deploy Your Service

```bash
# SSH into RunPod instance
ssh root@your-pod-ip -p 12345

# Clone your repo or upload files
git clone <your-repo>
cd ai-service

# Install dependencies
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Run service (expose to public)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Access from Your Mac

```bash
# Your Node.js app connects to:
AI_SERVICE_URL=https://your-pod-id-8000.proxy.runpod.net
```

**Cost**: ~$0.34/hour for RTX 4090 (only pay when running)

---

## 2️⃣ Modal (Serverless - No Server Management)

**Best for production with auto-scaling**

### Install Modal

```bash
pip install modal
modal token new
```

### Create `modal_deploy.py`

```python
import modal

stub = modal.Stub("deepfake-detection")

# Define image with dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi",
    "uvicorn",
    "torch",
    "torchvision",
    "Pillow",
    "imagehash",
    "pydantic"
)

@stub.function(
    image=image,
    gpu="T4",  # or "A100" for more power
    timeout=300
)
@modal.web_endpoint(method="POST")
def analyze(file: bytes):
    from app.services.inference import InferenceService
    from app.services.image_processing import ImageProcessor

    # Process image
    processor = ImageProcessor()
    image_tensor = processor.process_image(file)

    # Run inference
    service = InferenceService()
    result = service.predict(image_tensor)

    return result
```

### Deploy

```bash
modal deploy modal_deploy.py

# Returns URL like:
# https://your-username--deepfake-detection-analyze.modal.run
```

**Cost**: Pay only per request (~$0.0002 per inference)

---

## 3️⃣ Google Colab Pro (For Testing)

**Best for quick experiments**

### Setup

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Runtime → Change runtime type → T4 GPU
3. Upload your files or clone from GitHub

### Notebook

```python
# Install dependencies
!pip install fastapi uvicorn nest-asyncio pyngrok

# Clone your repo
!git clone <your-repo>
%cd ai-service

# Run service with public URL
import nest_asyncio
from pyngrok import ngrok
import uvicorn

nest_asyncio.apply()

# Create tunnel
public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")

# Run service
uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
```

**Cost**: $10/month (100 compute units)

---

## 4️⃣ AWS EC2 with GPU (Production)

**Best for enterprise/production deployments**

### Launch Instance

```bash
# Use AWS CLI or Console
# Instance type: g4dn.xlarge (cheapest GPU)
# AMI: Deep Learning AMI (Ubuntu)
```

### Deploy with Docker

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@ec2-ip

# Install Docker with NVIDIA runtime
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Clone and run
git clone <your-repo>
cd ai-service

# Build and run with GPU
docker build -t ai-service .
docker run -p 8000:8000 --gpus all ai-service
```

### Configure Security Group

- Inbound: Port 8000 from your IP
- Or use VPN/SSH tunnel

**Cost**: $0.526/hour (~$380/month if running 24/7)

---

## 5️⃣ Vast.ai (Cheapest Option)

**Best for budget-conscious development**

### Setup

```bash
# 1. Sign up at vast.ai
# 2. Search for instance with:
#    - GPU: RTX 3090 or RTX 4090
#    - Template: PyTorch
#    - Price: Sort by cheapest

# 3. SSH into instance
ssh root@ssh.vast.ai -p 12345

# 4. Deploy service
git clone <your-repo>
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Cost**: ~$0.20/hour for RTX 3090

---

## 6️⃣ Lambda Labs

**Best for ML-specific hosting**

### Setup

```bash
# 1. Reserve instance at lambdalabs.com
# 2. SSH into instance (comes with CUDA pre-installed)

ssh ubuntu@lambda-instance

# 3. Deploy
git clone <your-repo>
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Cost**: $1.10/hour for A100

---

## 🏗️ Hybrid Architecture (Recommended)

### Development Setup

```
┌─────────────┐
│   M1 Mac    │ ← Your development machine
│  (Node.js)  │
└──────┬──────┘
       │ HTTP
       ↓
┌─────────────┐
│  Cloud GPU  │ ← AI Service (Python + GPU)
│   RunPod    │
└─────────────┘
```

### Configuration

```javascript
// .env on your Mac
NODE_ENV=development
AI_SERVICE_URL=https://your-runpod-instance:8000

// Your Node.js app
const aiServiceUrl = process.env.AI_SERVICE_URL;
const response = await axios.post(
  `${aiServiceUrl}/analyze`,
  formData
);
```

---

## 💰 Cost Optimization Tips

### 1. Use Spot Instances

```bash
# AWS: 70% cheaper
# RunPod: "Spot" pricing
```

### 2. Auto-Shutdown

```bash
# RunPod: Auto-pause after 5 min idle
# AWS: Use Lambda or auto-scaling
```

### 3. Cache Results

```javascript
// Node.js - cache embeddings
const cacheKey = `embedding:${imageHash}`;
const cached = await redis.get(cacheKey);
if (cached) return cached;
```

### 4. Batch Processing

```python
# Process multiple images at once
# 8 images in one request ≈ same cost as 1
```

---

## 🔒 Security Best Practices

### 1. Private Network

```bash
# Use VPN or SSH tunnel
ssh -L 8000:localhost:8000 user@cloud-instance
```

### 2. API Authentication

```python
# Add to main.py
from fastapi import Header, HTTPException

@app.post("/analyze")
async def analyze(
    file: UploadFile,
    x_api_key: str = Header(None)
):
    if x_api_key != os.getenv("API_KEY"):
        raise HTTPException(401)
```

### 3. Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: "global")

@app.post("/analyze")
@limiter.limit("100/minute")
async def analyze(...):
    ...
```

---

## 📊 Monitoring

### Add to main.py

```python
import time
from prometheus_client import Counter, Histogram

REQUESTS = Counter('requests_total', 'Total requests')
INFERENCE_TIME = Histogram('inference_seconds', 'Inference time')

@app.post("/analyze")
async def analyze(...):
    REQUESTS.inc()
    start = time.time()

    # ... your code ...

    INFERENCE_TIME.observe(time.time() - start)
```

---

## 🎯 My Recommendation

**For your use case:**

1. **Development**: Use **RunPod** ($0.34/hr, pause when not using)
2. **Production**: Use **Modal** (serverless, auto-scales, pay per use)
3. **Testing**: Keep using **M1 Mac** (good enough for development)

### Why RunPod + Modal?

```
Development (RunPod):
├── Fast setup (2 min)
├── Cheap ($0.34/hr)
├── Easy to pause
└── SSH access for debugging

Production (Modal):
├── Auto-scaling (0 to 100+ GPUs)
├── Pay per request
├── No server management
└── Built-in load balancing
```

---

## 🚀 Quick Start with RunPod

```bash
# 1. Go to runpod.io → Sign up
# 2. Pods → Deploy → PyTorch template
# 3. Select GPU: RTX 4090 (or cheaper)
# 4. Click Deploy

# 5. Open Jupyter or SSH terminal
# 6. Run these commands:

git clone <your-repo>
cd ai-service
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 7. Get public URL from RunPod dashboard
# 8. Update your .env:
AI_SERVICE_URL=https://xxxx-8000.proxy.runpod.net
```

**Total time: 5 minutes**  
**Cost: ~$0.34/hour (only when running)**

---

Need help with any specific platform? Let me know!
