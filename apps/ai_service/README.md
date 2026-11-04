# AI service

Scores frames captured by the browser extension for signs of AI generation. Internal only: in production, `apps/api` calls it. For how detection works and why, see [ARCHITECTURE.md](../../ARCHITECTURE.md#ai-service-appsai_service) and [the research notes](../../docs/ai-video-detection-research.md).

## Setup

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
cp .env.example .env
```

On first start the service downloads about 4 GB of weights into `weights/`: GenD-PE, CLIP ViT-L/14, XCLIP-B/16 and YuNet. Only the 4 KB UnivFD probe is committed.

## Run

```sh
.venv/bin/uvicorn app.main:app --port 8000      # or `pnpm dev:ai` from the repo root
.venv/bin/python -m pytest -q                   # unit tests; no models needed
```

## API

`GET /health` lists the heads that loaded or failed, and the device.

`POST /analyze/video`:

```jsonc
{
  "video": { "width": 1280, "height": 720, "capture_method": "canvas" },   // or "tab_capture"
  "frames": [{ "data": "data:image/jpeg;base64,...", "timestamp": 3.2 }],  // sparse, up to 64
  "bursts": [{ "fps": 8, "frames": [{ "data": "...", "timestamp": 5.0 }] }] // consecutive, 16 at 8 fps
}
```

The response contains:

- `verdict`: `likely_ai`, `inconclusive` or `no_evidence`.
- `probability`: the fused chance of AI generation, or `null` if no head could score.
- `heads[]`: each head's `score`, `peak`, `frames_scored`, and the `reason` when it could not score.
- `quality`: usable frame and burst counts, plus flags such as `low_resolution`, `screen_capture` and `burst_static`.
- `calibrated`: false until the heads and the fuser are calibrated.

## Configuration

All settings are environment variables; see `.env.example`.

- **Choosing heads:** `ENABLED_HEADS` picks which heads load, for example `scene,temporal` to skip the face model.
- **Temporal head (D3):** it stays out of the verdict until `D3_MIDPOINT` is set. To calibrate it, point `scripts/calibrate_d3.py` at folders of real and AI videos that have been through the same platform encoding as production:

  ```sh
  .venv/bin/python -m scripts.calibrate_d3 --real data/real --fake data/ai --max-fpr 0.05
  ```
