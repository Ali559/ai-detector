# Plans

Forward-looking plans. For how the system works today, see [ARCHITECTURE.md](../ARCHITECTURE.md). For why detection is built the way it is, see [the research notes](../docs/ai-video-detection-research.md).

| Plan | Covers | Budget |
| --- | --- | --- |
| [cloud-inference.md](cloud-inference.md) | Renting a GPU to test the whole system from anywhere | $0–18/month on Modal; $8–11/month on RunPod |
| [training.md](training.md) | Data, tooling, evaluation and phases for training and calibrating the detectors | $0–5 to start; about $240 for full closed-generator coverage |

## Status

| Item | Code | Still to do |
| --- | --- | --- |
| Analysis through the API | ✓ `POST /api/detections`: auth, daily quota, saves results | Deploy the API somewhere; run `db:migrate` on Neon |
| Calibration | ✓ `tools/calibrate.py` → `calibration.json`, loaded by the service | Run it on real labelled video (training.md, phase 2) |
| Scene probe retraining | ✓ `training/extract_features.py` and `training/train_probe.py` | Collect data and run it (training.md, phases 1–2) |
| Cloud testing | ✓ `deploy/modal_app.py`, `deploy/runpod_setup.sh`, `SERVICE_TOKEN` | Create the Modal account and deploy (cloud-inference.md) |
