"""Run the AI service on Modal: a GPU that scales to zero when idle.

Modal bills per second and includes $30/month of free credit, which covers a
few hours of testing a week (see plans/cloud-inference.md). The FastAPI app
runs unchanged.

One-time setup (from apps/ai_service):

    pip install modal && modal setup
    modal secret create ai-detector SERVICE_TOKEN=$(openssl rand -hex 32)
    modal run deploy/modal_app.py::download_weights   # caches ~4 GB in a Volume

Deploy (prints the https://...modal.run URL):

    modal deploy deploy/modal_app.py

Then point the API at it: AI_SERVICE_URL=<that URL> and AI_SERVICE_TOKEN=<the
same token>. Stop paying entirely with `modal app stop ai-detector`.
"""

from pathlib import Path

import modal

SERVICE_ROOT = Path(__file__).resolve().parent.parent

# L4 (24 GB) is the best price/performance here; "T4" is ~25% cheaper and slower.
GPU = "L4"
# Keep the container warm this long after the last request, so a testing
# session doesn't pay for a cold start on every video. Billed while warm.
SCALEDOWN_SECONDS = 300

weights = modal.Volume.from_name("ai-detector-weights", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install_from_requirements(str(SERVICE_ROOT / "requirements.txt"))
    # Every Hugging Face / timm download lands in the Volume, not the image.
    .env({"WEIGHTS_DIR": "/weights", "HF_HOME": "/weights/hf"})
    .add_local_file(SERVICE_ROOT / "weights" / "univfd_fc.pth", "/root/weights/univfd_fc.pth")
)
if (SERVICE_ROOT / "calibration.json").exists():
    image = image.add_local_file(SERVICE_ROOT / "calibration.json", "/root/calibration.json")
image = image.add_local_python_source("app")

app = modal.App("ai-detector", image=image)


@app.function(gpu=GPU, volumes={"/weights": weights}, timeout=1800)
def download_weights():
    """Load every head once so its weights are cached in the Volume."""
    from app.config import get_settings
    from app.pipeline.detector import load_heads

    heads, failed = load_heads(get_settings())
    weights.commit()
    print("cached:", list(heads), "failed:", failed or "none")


@app.function(
    gpu=GPU,
    volumes={"/weights": weights},
    secrets=[modal.Secret.from_name("ai-detector", required_keys=["SERVICE_TOKEN"])],
    scaledown_window=SCALEDOWN_SECONDS,
    timeout=600,
)
@modal.concurrent(max_inputs=4)
@modal.asgi_app()
def web():
    from app.main import app as fastapi_app

    return fastapi_app
