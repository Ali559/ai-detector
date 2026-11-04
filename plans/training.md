# Plan: training and calibrating the detectors

**Goal:** turn v1's uncalibrated, partly off-the-shelf detectors into ones that are measured on modern AI video, calibrated for a low false-alarm rate, and cheap to retrain whenever a new generator appears.

**Approach:**

- **Don't train big models.** Freeze the foundation models and fit only small heads:
  - a 768→1 linear probe for the scene check;
  - Platt scaling per check;
  - a small fuser over the checks.
- **Spend on data, not compute.** Generator diversity matters far more than volume (see [the research notes](../docs/ai-video-detection-research.md)). The GPU work is a few hours of feature extraction per round.

This is not legal advice. Dataset and generator licences are summarised below from their own pages. Have them reviewed before selling anything trained on them.

## 1. What gets trained, and with which tool

| Component | What's fitted | Tool (in `apps/ai_service`) | Compute |
| --- | --- | --- | --- |
| **Scene check** | 768→1 linear probe on frozen CLIP ViT-L/14 crop features | `training/extract_features.py` (GPU), then `training/train_probe.py` (CPU, minutes) | About 1–3 GPU-hours per 1,000 videos |
| **Per-check calibration** | Platt scaling for face, scene and D3 | `tools/calibrate.py run` (GPU), then `tools/calibrate.py fit` (CPU, seconds) | About 1 GPU-hour per 500 videos |
| **Fuser and verdict bands** | Logistic regression over the calibrated checks, plus thresholds for target error rates | `tools/calibrate.py fit` | CPU |
| Face check (GenD) | Nothing in v1: the pretrained model is used as-is | (fine-tuning is phase 3) | – |
| Motion check (D3) | Nothing to train; calibration only | as above | – |

Every tool reads the same **manifest CSV** (`path,label,generator,split`; see `tools/manifest.py`). Every tool samples frames through `tools/sampling.py`, which copies the extension's capture exactly: sparse frames plus 16-frame bursts at 8 fps, JPEG at quality 95, capped at 1920 px.

The rule: **training and calibration only ever see frames that went through the production path.**

## 2. Data layout

```
data/                         # not in git; on a laptop disk or a RunPod network volume
  raw/
    real/<source>/*.mp4       # e.g. real/phone-ali/, real/aigvdbench-openvid/
    fake/<generator>/*.mp4    # e.g. fake/wan2.2-ti2v-5b/, fake/veo3.1-fast/
  manifests/
    train.csv                 # scene probe training (split column empty or train/val)
    calib.csv                 # calibration: disjoint from train.csv; split train/test
    eval-df26.csv             # final evaluation only; never used for fitting
runs/
  2026-11-scene-v1/
    features/                 # one .npz per video (~30 KB): delete the videos afterwards
    probe/scene_probe.pth     # → SCENE_HEAD_WEIGHTS
    probe/metrics.json
  2026-11-calib-v1/
    scores.csv
    calibration.json          # → apps/ai_service/calibration.json
```

**Rules:**

1. **One video goes in exactly one of train / calib / eval.** The manifests are disjoint.
2. **Split by video, never by frame.** The tools do this.
3. **The generator name is the most important column.** It drives per-generator metrics and held-out-generator tests. Use specific names like `wan2.2-ti2v-5b` and `veo3.1-fast`, not "fake".
4. **Real videos are labelled by source** (`phone-ali`, `aigvdbench-openvid`, and so on), so per-source false-alarm rates show up too.

## 3. Data recipe

Ordered from cheapest to most expensive. Each tier is usable on its own.

### Tier 0: $0, research only

| Use | Data | Size | Licence |
| --- | --- | --- | --- |
| Fakes, train and calib | **AIGVDBench**: about 100 videos from each of ~12 open-source generators (Wan 2.1, CogVideoX, Hunyuan, EasyAnimate, Open-Sora, Pyramid-Flow…) | About 23 GB | CC BY 4.0 dataset; the terms of the underlying source videos are unverified |
| Reals, train and calib | **AIGVDBench's OpenVid-HD reals** (they match the fakes' content and encoding) | About 20 GB | OpenVid's own card says "research and non-commercial" |
| Final eval | **DF26**: 2,691 clips, 720p, covering Veo 3.1, Kling 3.0, Wan 2.6, Grok Imagine, Hunyuan 1.5 and LTX-2.3, plus real talking heads | 3.6 GB | **Evaluation only, no training.** Don't calibrate on it either |

This tier gets real numbers on modern generators quickly. **A product can't ship on it,** because the reals are research-only.

### Tier 1: about $15–40, commercially cleaner

- **Self-generated fakes:** about 300 clips each from **Wan 2.2 TI2V-5B** (Apache 2.0; "no rights over generated contents") and **LTX-2** (free under $10M revenue).
  - Wan 2.2 TI2V-5B takes under 9 minutes per 720p clip on a 24 GB GPU: about 45 GPU-hours × $0.34 (Community 4090) ≈ **$15**.
  - Use prompts from VidProM's prompt CSV (text only) so the content varies.
- **Self-recorded real video:**
  - **This is the real bottleneck.** No large real-video source is cleared for commercial ML training: Pexels and Pixabay both forbid it.
  - Record 300–1,000 short clips on phones. Cover indoor and outdoor scenes, people, animals, screens and text, day and night, still and moving cameras.
  - Upload some to YouTube or TikTok as unlisted, then capture them back through the extension's path. That gives real platform compression.
- **Don't use HunyuanVideo outputs.** Its licence forbids using them to improve another AI model, and excludes the EU, UK and South Korea.

### Tier 2: about $220–370, closed generators for calibration and eval

Buy about 100 clips (5 s each) from each commercial generator. Split each generator's clips half for calibration, half held out for test:

| Generator | About $ per 100 clips |
| --- | --- |
| Veo 3.1 Fast | $50 (full Veo 3.1: $200) |
| Kling 3.0 | $50–70 |
| Runway Gen-4.5 | $60 |
| MiniMax Hailuo 2.3 | $28 |
| Luma Ray 3.2 | $30 |

The Sora 2 API shut down on 24 Sep 2026; DF26 doesn't include Sora 2 either.

Check each vendor's terms on using outputs to train a model. Google's say no models "that compete with the Services". A detector arguably doesn't compete with a video generator, but get that confirmed.

### How much is enough

- Linear probes on CLIP features are data-efficient. Cozzolino et al. (CVPRW 2024) found 1k–10k paired images near-optimal, and about 100 already competitive on post-processed data. UnivFD showed little loss from cutting its 720k training images by 3–4×.
- **Target for the scene probe: about 2k real and about 2k fake videos, 8 frames each.**
- **Target for calibration: about 300 real and about 300 fake videos, spread across generators.** At least 20 per class is the tool's hard floor.
- These are image-level results extrapolated to video frames. Measure your own curve by training on 25%, 50% and 100% of the data.

## 4. The pipeline, step by step

All commands run from `apps/ai_service` on a GPU box. See [cloud-inference.md](cloud-inference.md) for where to rent one.

```bash
# 0. Build manifests: one row per video. Generator names matter.
#    data/manifests/train.csv, calib.csv, eval-df26.csv

# 1. Scene probe features. Re-encode like a platform, twice per video, as augmentation.
.venv/bin/python -m training.extract_features \
    --manifest data/manifests/train.csv --out runs/scene-v1/features \
    --frames 8 --simulate-platform --platform-copies 2

# 2. Train the probe (CPU). Hold out one or two generators to see how it handles unseen ones.
.venv/bin/python -m training.train_probe \
    --features runs/scene-v1/features --out runs/scene-v1/probe \
    --holdout-generators wan2.2-ti2v-5b
#    Then retrain without --holdout-generators to ship the probe that saw everything.

# 3. Calibrate, using the new probe.
export SCENE_HEAD_WEIGHTS=runs/scene-v1/probe/scene_probe.pth
.venv/bin/python -m tools.calibrate run --manifest data/manifests/calib.csv \
    --out runs/calib-v1/scores.csv --simulate-platform
.venv/bin/python -m tools.calibrate fit --scores runs/calib-v1/scores.csv \
    --out runs/calib-v1/calibration.json --max-fpr 0.05 --max-fnr 0.2

# 4. Final evaluation on DF26: scored and reported, never fitted on.
.venv/bin/python -m tools.calibrate run --manifest data/manifests/eval-df26.csv \
    --out runs/eval-df26/scores.csv
.venv/bin/python -m tools.calibrate eval --scores runs/eval-df26/scores.csv \
    --calibration runs/calib-v1/calibration.json --out runs/eval-df26/metrics.json

# 5. Ship it: copy the probe to weights/scene_probe.pth, set SCENE_HEAD_WEIGHTS,
#    commit calibration.json next to app/, and redeploy.
```

**Interruptions are fine:** both `extract_features` and `calibrate run` skip videos they've already done. That makes interruptible GPUs (Vast.ai interruptible, RunPod spot) safe to use.

## 5. How to judge a model

**Ship only if every item below holds on held-out data.** Otherwise keep the previous version.

1. **False alarms on real video at or below 5%:** `real_flagged_likely_ai` in the calibration report. This is the number that protects users from being wrongly accused.
2. **Every real source stays under that 5%,** not just the pooled average. A pooled AUC hides per-source failures.
3. **Detection (`likely_ai`) at or above 50% for each fake generator in the calibration test split.** List generators where it's lower in the release notes.
4. **The held-out-generator run of `train_probe`** reports how well the probe catches a generator it never saw. Expect this to be much lower than for seen generators. It's the honest estimate for next month's new model.
5. **DF26 per-generator results** are recorded in the release notes as the external benchmark.

## 6. Compute plan and costs

| Job | Where | Cost |
| --- | --- | --- |
| Feature extraction, about 4k videos × 2 re-encodes | **Kaggle free GPU** (about 30 GPU-hours a week; third-party figure) if the data fits in a Kaggle dataset; otherwise a RunPod Community A5000/3090 | $0, or about 6 h × $0.22 ≈ **$1.50** |
| Calibration scoring, about 600 videos | Same | $0–1 |
| Probe training and `calibrate fit` | Your laptop | $0 |
| Self-generated fakes, Tier 1 | RunPod Community 4090 | about $15 |
| Commercial API clips, Tier 2 | Vendor APIs | about $220 |
| Storage | 10–50 GB RunPod network volume at $0.07/GB/month, deleted after features are extracted | $1–4 per month |

**Totals:** Tier 0 costs **about $0–5**. Tier 1 adds **about $20**. Tier 2 adds **about $220**. Compute is never the expensive part; data is.

## 7. Phases

| Phase | Done when | Spend |
| --- | --- | --- |
| **1. Baseline numbers** | The current UnivFD probe and uncalibrated fusion are measured on DF26 and a small AIGVDBench calib set. This is the "before" picture | $0 |
| **2. Scene probe v1 + calibration v1** | Trained on Tier 0 (research) or Tier 1 (commercial) data; ships when section 5 passes; `calibration.json` committed | $0–40 |
| **3. Closed generators** | Tier 2 clips added to calibration; DF26 and the API test split reported per generator | about $220 |
| **4. Face check fine-tune** | GenD's LayerNorm-only fine-tune on licensed face data (DeepSpeak v2 needs a paid licence for commercial use). Only if phase 3 shows face swaps being missed | TBD |
| **5. Flywheel** | User "this was wrong" reports become new labelled data. Each new major generator gets 100 clips, a feature extraction run and a probe refit. Retrain monthly or on each major release | about $50 per new generator |

## 8. Risks

- **The real class is the hard part.** If reals come from a different camera, codec or kind of content than the fakes, the probe learns "phone footage vs AI" rather than "real vs AI". Match content and encoding, and always use `--simulate-platform` on both classes.
- **Watermark shortcuts.** Crops already keep out of the outer 10% of each side, where Sora, Veo and Kling place their logos. Spot-check the clips for watermarks in the middle of the frame anyway.
- **Calibration drifts as generators change.** Re-run `tools/calibrate.py` whenever the probe or a check changes. Treat `calibration.json` as part of the model version.
- **Licences.** Track the licence of every source in the manifest's generator naming and in the release notes. Keep research-only data out of shipped weights.

## Sources

- Datasets:
  - AIGVDBench: https://huggingface.co/datasets/AIGVDBench/AIGVDBench · https://github.com/LongMa-2025/AIGVDBench
  - DF26: https://huggingface.co/datasets/DF26/DF26
  - OpenVid-1M: https://huggingface.co/datasets/nkp37/OpenVid-1M
  - VidProM: https://huggingface.co/datasets/WenhaoWang/VidProM
  - DeepSpeak v2: https://huggingface.co/datasets/faridlab/deepspeak_v2
- Generator licences:
  - Wan 2.2: https://github.com/Wan-Video/Wan2.2
  - HunyuanVideo 1.5: https://huggingface.co/tencent/HunyuanVideo-1.5/blob/main/LICENSE
  - LTX-2: https://github.com/Lightricks/LTX-2
- API pricing:
  - MiniMax: https://platform.minimax.io/docs/pricing/pay-as-you-go
  - Luma: https://docs.agents.lumalabs.ai/guides/pricing/
  - Veo, Kling and Runway prices are from secondary sources and unverified.
- Stock footage terms:
  - Pexels: https://help.pexels.com/hc/vi-vn/articles/900005880463
  - Pixabay: https://pixabay.com/service/terms/
- Data efficiency:
  - Cozzolino et al. 2024: https://arxiv.org/html/2312.00195v2
  - UnivFD: https://arxiv.org/abs/2302.10174
- Google API terms: https://ai.google.dev/gemini-api/terms
