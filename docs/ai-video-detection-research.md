# Detecting AI-generated video from extracted frames

Research notes (November 2026) on how to decide whether a video is authentic or AI-generated, given the frames our extension can grab from a `<video>` element. This feeds the "Detection approach" section of [ARCHITECTURE.md](../ARCHITECTURE.md).

Claims marked _(unverified)_ come from memory or secondary sources and should be checked before we rely on them.

## Bottom line

1. **No detector reliably generalises to today's commercial generators** (Veo 3.1, Kling 3.0, Sora 2, Wan 2.6, and others). Models trained on older data score close to chance on new generators. What we ship is a triage tool with calibrated uncertainty, not a lie detector. We will need to retrain continuously.
2. **The strongest family right now is frame-level classifiers on frozen foundation-model features** (CLIP, DINOv2/v3, Perception Encoder), even for video. Examples are GenD and Effort. In AIGVDBench (CVPR 2026), purpose-built video detectors came out mid-tier.
3. **Training data matters more than architecture.** Adding frames from just one modern generator lifted cross-generator AUROC by about 6 points in DF26.
4. **Provenance beats classification when it is present**, but almost none of it survives a canvas frame grab. Only pixel-level watermarks do.
5. **The biggest domain shift is compression.** Platform re-encoding plus our own JPEG step destroys exactly the artefacts many detectors look for. Train on frames that went through the same capture path we use in production.

## 1. Which detector for which kind of fake

| Kind of fake | Examples | What works |
| --- | --- | --- |
| **Face swap, reenactment, lip-sync.** Real video with the face region changed. | DeepFaceLab, FaceFusion, LivePortrait | A face detector and crop, then a face-forensics model (GenD, Effort, SBI, TALL, FTCN). |
| **Fully synthetic** text-to-video or image-to-video | Sora 2, Veo 3.1, Kling, Runway, Wan, Hunyuan | Full-frame detectors trained on generated-video corpora, plus temporal methods. Face-only models fail here: FF++-trained face detectors collapse on synthetic talking heads (DF26). |
| **AI-edited real video**: inpainting, restyling, object insertion | Runway Aleph-style video-to-video | Hardest case. Needs segment- or region-level scoring. Off-the-shelf models lost about 31% accuracy on videos mixing real and fake faces (Deepfake-Eval-2024). |

**Consequence for us:** run two heads, a **face head** on face crops and a **scene head** on full frames, and combine them. A face-swap model saying "real" about a Veo clip means nothing.

## 2. Frame-level detectors

| Model | Idea | Usable? |
| --- | --- | --- |
| **GenD** (2025) | Tunes only the LayerNorm parameters of CLIP, Perception Encoder or DINOv3, with metric learning. Best cross-dataset AUROC across 14 deepfake datasets. Best on DF26, though only at 69.7 AUROC. | **Yes.** MIT license, Hugging Face checkpoints (`yermandy/GenD_PE_L`, `GenD_CLIP_L_14`, `GenD_DINOv3_L`). Expects faces cropped by its own `detector.py`. |
| **Effort** (ICML 2025) | Freezes the main SVD subspace of CLIP and tunes only the residual. Best detector on closed-source generators in AIGVDBench (94.05 AUC). | Repo license unverified. The copy inside DeepfakeBench is CC BY-NC (non-commercial). |
| **UnivFD** (CVPR 2023) | A linear probe on frozen CLIP ViT-L/14. | Yes (MIT). Dated, but a cheap ensemble member and a good first baseline. |
| **ForgeLens** | Best average on open-source generators in AIGVDBench (91.82). | Repo and license not checked. |
| Frequency / spectral (F3Net, SPSL, NPR) | Upsampling and decoder fingerprints. | Auxiliary features only. Codec re-encoding wipes these out. |
| Diffusion reconstruction (DIRE, AEROBLADE) | How well a diffusion model or autoencoder reconstructs the frame. | Not for us: expensive, sensitive to JPEG compression and tied to one autoencoder _(unverified)_. |

Zero-shot vision-language models (asking an LLM "is this AI?") scored near chance, about 50–55%, in AIGVDBench. They are useful for _explaining_ evidence, not for issuing the verdict.

## 3. Temporal and multi-frame methods

Per-frame artefacts are fading as generators improve, and codecs erase them. Temporal cues tend to survive compression better: physically impossible motion, texture flicker, identity drift, and unnatural second-order motion. The evidence is mixed, though. On DF26, temporal detectors that scored 92–94 AUROC on older benchmarks dropped to 48–62, below frame-based GenD. **Treat temporal models as a complementary signal, not a replacement.**

| Model | Input it needs | Notes |
| --- | --- | --- |
| **D3** (ICCV 2025) | Consecutive frames, run through a feature encoder (XCLIP in the repo example) | **Training-free.** The score is the spread of second-order differences between feature frames. MIT license. Claims robustness to post-processing. The best cheap first temporal signal. |
| **V-PVP** (2026) | A video backbone with a small patch-velocity readout | 95.28 AUC on AIGVDBench with the backbone frozen. Argues that global pooling throws motion cues away. Code license not checked. A v2 candidate. |
| **AIGVDet** (2024) | RGB frames plus RAFT optical flow from **truly consecutive** frames at native fps | Two ResNet-50 branches. Reported robust up to CRF 28. License unverified. |
| DeMamba (2024) | A frame sequence of CLIP/XCLIP features | Apache-2.0. Introduced the GenVideo dataset. Mid-tier in AIGVDBench. Weights release unclear. |
| DeCoF, TALL, FTCN | Sampled or consecutive frames, or face clips | Older. FTCN fell from 0.87 to 0.50 AUC on in-the-wild data. |

**What this means for capture.** The extension needs two sampling modes:

- **Sparse:** 16–32 frames spread uniformly across the clip, for the frame classifiers. Both DF26 and AIGVDBench use 32-frame sampling.
- **Bursts:** one or two runs of 8–16 _consecutive_ frames at native frame rate, for temporal models. Capture them with `requestVideoFrameCallback` during normal playback rather than by seeking.

Today's content script seeks in steps of at least 0.5 s and captures 3 frames by default. That covers neither mode well.

## 4. Datasets and benchmarks

**Training data for synthetic video:**

- GenVideo: about 1M fake and 1.2M real videos.
- **GenVidBench**: about 6M videos, including Sora and Kling.
- **AIGVDBench**: 31 generators, about 440k videos.
- **DF26**: synthetic talking heads. The open subset is for training; the closed-generator subset is evaluation-only. Access is gated on Hugging Face.
- **RobustSora**: a study of watermark shortcuts.
- **RA-Bench**: crisis-event fakes plus social-media spread.

**Face deepfakes:** FaceForensics++, DFDC, Celeb-DF v2 / CelebDF++, DeepSpeak v2. These are mostly accessed through DeepfakeBench, which is non-commercial.

**In-the-wild evaluation:** **Deepfake-Eval-2024** has 45 hours of video from 88 sites in 52 languages.

- Detectors dropped sharply on it: GenConViT from 0.96 to 0.63 AUC, FTCN from 0.87 to 0.50.
- Fine-tuning on part of it brought GenConViT back to 0.82.
- The best commercial detector reached about 0.79 AUC, still below human forensic analysts.

Licenses for most of these datasets are unverified. Check each one before any commercial use.

## 5. Provenance signals

| Signal | Survives our frame grab? | Can we check it? |
| --- | --- | --- |
| **C2PA Content Credentials**, a signed manifest in the MP4 container | **No.** Container metadata is gone once we draw to a canvas. | Only by fetching the original file, which is usually impossible with blob/MSE streams, or by reading the platform's own label. YouTube's "Captured with a camera" is one such label. |
| **SynthID**, Google's pixel watermark on Veo and Imagen output | **In principle yes**, although repeated recompression weakens it. | **No public API.** Verification is only through the Gemini app or synthid.com, and API access is for partners only _(unverified)_. |
| **Meta Video Seal** and **Adobe TrustMark** (open watermarks) | Yes | Yes, with open decoders. Cheap to run, but few generators embed them, so hits will be rare. |
| **Visible logos** (Sora, Veo, Kling) | Yes | A logo detector can find them. A real signal, but trivially cropped. |

**Warning (RobustSora):** detectors learn visible watermarks as a shortcut, and removing the watermark cost up to 14 points on Sora 2. During training, mask or crop watermark regions, or add fake watermarks to real video. Report logo hits as their own, explicitly labelled signal.

## 6. Pitfalls in our pipeline

1. **Tainted canvases and DRM.**
   - A cross-origin video without CORS headers taints the canvas, and `toDataURL` throws.
   - DRM (EME) video renders black.
   - Fallbacks are `tabs.captureVisibleTab` (rate-limited, about 2 calls/s _(unverified)_) or `tabCapture`. Both produce _screen-captured_ frames, which are display-scaled and may include overlays.
   - Tag every frame with its capture method, and include screen-capture conditions in training augmentation.
2. **Compression is the main domain shift.**
   - Adaptive streaming may serve 360p. Send `videoWidth`/`videoHeight` with the frames and lower confidence on low-resolution input.
   - Send PNG or JPEG at q≥95. Our current q=0.8 adds a second lossy step.
3. **Format shortcuts.** Real and fake training video must go through _identical_ encode → decode → canvas → image steps. Otherwise the model learns codec differences instead of generation artefacts. AIGVDBench re-encodes everything to H.264 for this reason.
4. **Resizing.** Never upscale. Use crops or tiles at the model's native resolution rather than squashing the whole frame to 224×224, which is what `image_processing.py` does today. Face models need the exact crop margin their repo expects.
5. **Sampling hygiene.** Skip black, intro and ad frames. Detect shot boundaries and sample within shots.
6. **Face-detector licensing.** InsightFace and RetinaFace pretrained weights are non-commercial. MediaPipe and OpenCV YuNet are permissive _(verify)_. Handle frames with no face or several faces explicitly.
7. **Calibration.**
   - Sigmoid outputs are not probabilities after domain shift.
   - Calibrate with temperature or isotonic scaling on a held-out, recompressed, in-the-wild set.
   - Set the threshold for a target **false-positive rate**. Calling a real video fake is the costlier mistake, and humans already misjudge about 24% of real videos (DF26).
8. **Per-slice evaluation.** A pooled AUC hides failures on particular generators. Report results per generator and per platform.
9. **Adversaries win.** Perturbations, recompression, cropping and watermark removal all defeat current detectors. Present results as triage evidence, never proof.

## 7. Recommended plan

### v1: weeks of work, permissive licenses only

**Extension**
- Capture 16–32 uniformly spaced frames, plus 2 bursts of 8 consecutive frames via `requestVideoFrameCallback`.
- Fall back to `captureVisibleTab` when the canvas is tainted.
- Send PNG at native resolution with this metadata: page host, `videoWidth`/`videoHeight`, capture method, timestamps.

**AI service** (a pipeline of independent heads; each one reports its own score)
1. **Quality gate:** resolution, blur, black frames, shot detection. Low quality lowers the confidence ceiling.
2. **Face head:** MediaPipe or YuNet face crops → **GenD-PE** (MIT, pretrained weights available).
3. **Scene head:** frozen CLIP, DINOv2/v3 or PE features → a linear or LayerNorm-tuned head in the style of UnivFD or GenD.
   - Train on AIGVDBench, GenVidBench, GenVideo and DF26's open subset, with real video from the same platforms we target.
   - Avoid DeepfakeBench code (non-commercial).
4. **Temporal head:** **D3** (MIT, training-free) on the bursts.
5. **Watermarks:** Video Seal and TrustMark decoders, plus a visible-logo detector. Each is reported as a separate signal.
6. **Aggregate:**
   - Within each head, combine per-frame logits robustly. The mean works, and a top-k mean (k ≈ 25%) catches partial edits better.
   - Combine heads with a small logistic-regression fuser trained on held-out data.
   - Calibrate, then map to **likely AI / inconclusive / no evidence found**, with per-head evidence attached.

**API contract**

`detection_results.detection_methods_used` and `frame_analyses.provider_results` already have room for per-head scores. Store every head's output, the input-quality flags and the model versions, so we can re-evaluate later.

**Extension UI**

Replace the binary "AI Generated / Authentic" with the three bands. Show which signals fired and the input-quality caveats.

### v2

- **Motion-aware video model:** fine-tune a video backbone with a motion-aware readout (V-PVP on a VideoMAE- or V-JEPA-class model) on consecutive clips.
- **Data flywheel:**
  - Script generation from each new commercial generator as it launches.
  - Add user-reported mistakes from the `reports` table, labelled by a reviewer.
  - Retrain monthly, with per-generator and per-platform regression tests.
- **Training augmentation:** simulate the whole pipeline (platform-style H.264/AV1 at several CRFs, rescaling, screen capture), with watermark masking.
- **Localisation for edited real video:** top-k segments, and disagreement between the face score and the background score.
- **Explanations:** an optional vision-language-model layer (Skyra-style) that _describes_ the evidence but never issues the verdict.
- **Vendor verification:** SynthID if partner access becomes available, and C2PA whenever the original file URL can be fetched.

## Open questions

- Licenses for Effort, ForgeLens, AIGVDet, V-PVP, Video Seal, GenVidBench, AIGVDBench and GenVideo.
- Exact input specifications for D3 (frame count and fps), TALL and FTCN.
- Whether DeMamba's weights are released.
- SynthID API availability and platform C2PA-stripping behaviour (only conflicting secondary sources found).

## Sources

- AIGVDBench (CVPR 2026): https://arxiv.org/html/2601.11035 · https://github.com/LongMa-2025/AIGVDBench
- DF26: https://arxiv.org/html/2609.07369v1 · https://huggingface.co/datasets/DF26/DF26
- Deepfake-Eval-2024: https://arxiv.org/html/2503.02857v4 · https://github.com/nuriachandra/Deepfake-Eval-2024
- GenVidBench: https://arxiv.org/abs/2501.11340
- RobustSora: https://arxiv.org/abs/2512.10248
- RA-Bench: https://arxiv.org/abs/2608.14391
- GenD: https://arxiv.org/html/2508.06248v3 · https://github.com/yermandy/GenD
- Effort: https://arxiv.org/abs/2411.15633 · https://github.com/YZY-stack/Effort-AIGI-Detection
- UnivFD: https://arxiv.org/abs/2302.10174 · https://github.com/WisconsinAIVision/UniversalFakeDetect
- DeepfakeBench (CC BY-NC): https://github.com/SCLBD/DeepfakeBench
- D3: https://arxiv.org/abs/2508.00701 · https://github.com/Zig-HS/D3
- V-PVP: https://arxiv.org/abs/2607.15321 · https://github.com/manic-cui/Rethinking-the-readout
- DeMamba / GenVideo: https://arxiv.org/abs/2405.19707 · https://github.com/chenhaoxing/DeMamba
- AIGVDet: https://arxiv.org/abs/2403.16638 · https://github.com/multimediaFor/AIGVDet
- DeCoF: https://arxiv.org/abs/2402.02085
- TALL: https://arxiv.org/abs/2307.07494 · FTCN: https://github.com/yinglinzheng/FTCN
- Compression robustness (NAMP): https://arxiv.org/pdf/2606.16742
- Skyra: https://arxiv.org/abs/2512.15693
- SynthID verification: https://support.google.com/gemini/answer/16722517 · https://blog.google/technology/ai/verify-google-ai-videos-gemini-app
- OpenAI provenance: https://openai.com/index/advancing-content-provenance
- C2PA durable credentials: https://contentauthenticity.org/blog/durable-content-credentials
- TrustMark: https://opensource.contentauthenticity.org/docs/trustmark/c2pa/
- Video Seal: https://github.com/facebookresearch/videoseal
- Canvas tainting and DRM: https://docs.theoplayer.com/api-reference/web/theoplayer.canvas.md
