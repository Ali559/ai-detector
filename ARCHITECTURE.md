# Architecture

AI Detector tells a user whether a video playing in their browser is authentic or AI-generated. A browser extension samples frames from the video and a backend scores them.

This document describes the system as it is today, where it is headed, and the gaps between the two. For the research behind the detection approach, see [docs/ai-video-detection-research.md](docs/ai-video-detection-research.md).

## Overview

```
┌────────────────────────── Browser ──────────────────────────┐
│                                                             │
│  Web page with <video>                                      │
│        ▲                                                    │
│        │ drawImage → canvas → JPEG (base64)                 │
│  ┌─────┴──────────┐   runtime     ┌──────────────┐          │
│  │ content script │◀──messages───▶│  background  │          │
│  └────────────────┘               └──────▲───────┘          │
│                                          │ runtime messages │
│                                   ┌──────┴───────┐          │
│                                   │ popup (Vue)  │          │
│                                   └──────┬───────┘          │
└──────────────────────────────────────────┼──────────────────┘
                                           │ HTTPS (planned)
                                  ┌────────▼────────┐      ┌────────────┐
                                  │   apps/api      │─────▶│ PostgreSQL │
                                  │ Fastify + auth  │      └────────────┘
                                  └────────┬────────┘      ┌────────────┐
                                           │ HTTP (planned)│   Redis    │
                                  ┌────────▼────────┐      │ (optional) │
                                  │ apps/ai_service │      └────────────┘
                                  │ FastAPI + torch │
                                  └─────────────────┘
```

The design has three parts, each with a single responsibility:

| Part | Responsibility | Never does |
| --- | --- | --- |
| Extension | Find the video, capture frames, show results | Run models; store secrets beyond a session token |
| API | Auth, quotas, billing, persistence, orchestration | Run models |
| AI service | Turn frames into scores | Know about users, auth or billing |

The AI service is internal-only. Only the API talks to it, and the API is the only public surface.

## Repository layout

A pnpm workspace (`pnpm-workspace.yaml`) holds the two JS packages. The Python service sits alongside and is managed with pip/venv.

```
apps/
  extension/    @ai-detector/extension  Vue 3 + Vite + Tailwind 4, shadcn-vue (reka-ui)
  api/          @ai-detector/api        Fastify 5, better-auth, Drizzle ORM, PostgreSQL
  ai_service/   (Python)                FastAPI, PyTorch, Pillow, imagehash
docker-compose.yml                      api + ai_service + postgres + redis
```

Run everything from the repo root: `pnpm dev:extension`, `pnpm dev:api`, `pnpm build`, `pnpm lint`.

## Extension (`apps/extension`)

A Manifest V2 extension that uses the WebExtension `browser.*` API (Firefox-first; `@types/firefox-webext-browser`). Vite builds three entry points into `dist/`: `popup.js`, `background.js` and `content.js` (see `vite.config.ts`).

### Components

- **Content script**: `src/content/content.ts`. Injected into every page (`<all_urls>`). When the popup sends `start`, it:
  1. Finds all `<video>` elements, including inside shadow roots, and picks the first one that is playing and has decoded data.
  2. Captures a **burst** of 16 consecutive frames at 8 fps from the current position, using `requestVideoFrameCallback` during normal playback. This is the input D3 was designed for.
  3. Captures 8–32 **sparse** frames spread across the whole video, skipping the first and last 2%. For live streams, it samples once a second during playback.
  4. Captures a second burst at 60% of the way through, if the video is at least 20 s long.
  5. Restores the original playback position and play/pause state, then sends `extraction-completed` with the video's metadata.

  Frames are drawn at the rendition's native resolution (capped at 1920 px on the long side) and encoded as JPEG at quality 0.95. Each one streams back as an `extracted` message as soon as it is captured.

  If the canvas is tainted (a cross-origin video without CORS), the content script switches to **tab capture**: it asks the background script for a screenshot of the visible tab and crops it to the video. Tab capture is rate-limited to about 2 calls per second, so bursts are skipped in this mode, and every frame is tagged `captureMethod: 'tab_capture'`.
- **Background script**: `src/background/background.ts`. Relays `start` from the popup to the active tab's content script. It also answers `capture-visible-tab`, because content scripts cannot call `tabs.captureVisibleTab` themselves.
- **Popup**: `src/popup/App.vue` plus `src/Views/*`. A Vue app with a hash router and Pinia.
  - `AuthView` holds the login and signup tabs.
  - `HomeView` and `MainContent.vue` drive a small state machine: `idle → extracting → extracted → analyzing → completed`. Each state has its own card component in `src/components/molecules/Home/`.
  - `src/lib/analysis.ts` posts the frames to the AI service and returns its result. The URL comes from `VITE_ANALYSIS_URL` and defaults to `http://localhost:8000/analyze/video`.
  - `AnalysisCompleteCard.vue` shows the verdict band, the fused probability, each head's score or the reason it could not score, and any input-quality flags.

### Message protocol

Messages are defined in `src/types/index.ts` (`ResponseType`, `IVideoFrame`, `IExtractionResponse`).

| Message | From → To | Payload |
| --- | --- | --- |
| `start` | popup → background → content | `frameCount` (number of sparse frames) |
| `extracted` | content → popup | `videoId`, `data: IVideoFrame` (base64 JPEG, size, timestamp, `kind: 'sparse' \| 'burst'`, `burstIndex`, `captureMethod`) |
| `extraction-completed` | content → popup | `videoId`, `frameCount`, `meta: IVideoMeta` (page URL, rendition size, duration, capture method, burst fps) |
| `capture-visible-tab` | content → background | none. Returns a PNG data URL of the visible tab |
| `error` | any → popup | `error` string |

## API (`apps/api`)

A Fastify 5 server (`src/server.ts`, `src/app.ts`) using the TypeBox type provider. Plugins are registered in order:

1. **CORS**: origin comes from `CORS_ORIGIN`, defaulting to `*`.
2. **Database plugin** (`src/plugins/database.plugin.ts`): opens a `pg` pool on `DATABASE_URL`, checks the connection, and decorates `fastify.db` with a Drizzle instance.
3. **Auth plugin** (`src/plugins/auth.plugin.ts`): sets up better-auth with the Drizzle adapter, email and password sign-in, and email verification, and decorates `fastify.auth`.
4. **Routes** under `/api`:
   - `POST /api/auth/signup/email`
   - `POST /api/auth/signin/email`. Returns `{ user, token }` and sets the `Authorization` header.

### Data model

Defined in `src/schemas/schema.ts`; Drizzle Kit handles migrations (`pnpm --filter @ai-detector/api db:*`). The schema is designed ahead of the code:

- **Identity**: `users` (includes tier and daily/monthly usage counters), `accounts` (password and OAuth providers), `sessions`.
- **Detection**:
  - `detection_results`: one row per analysed video, with the overall score, confidence level, methods used and user feedback.
  - `frame_analyses`: per-frame scores and per-provider results, keyed by frame hash.
  - `detection_cache`: scores for frames seen before, keyed by hash, with an expiry.
- **Operations**: `usage_logs`, `api_keys`, `webhooks`, `reports` (user-reported false positives and negatives).
- **Billing**: `subscriptions`, `invoices`, `payments`, `pricing_plans`, `payment_methods`.

## AI service (`apps/ai_service`)

A FastAPI app (`app/main.py`). On startup it loads each enabled head (`ENABLED_HEADS`) on CUDA, MPS or CPU. A head that fails to load is reported in `/health` and in every result, rather than stopping the service.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Which heads loaded, which failed, and the device |
| `POST /analyze/video` | Sparse frames plus bursts plus video metadata → verdict, per-head scores and input-quality report |

The request and response schemas are in `app/schemas.py`. The pipeline lives in `app/pipeline/`:

```
decode (frames.py) → quality gate (quality.py) → face / scene / temporal heads → fuse (aggregate.py)
```

- **Quality gate** (`quality.py`):
  - Drops frames that are blank or smaller than 144 px.
  - Flags low resolution, blur and screen capture.
  - Rejects bursts that contain a scene cut or no motion. A static burst would look "too smooth" to D3, which reads smoothness as a sign of AI.
- **Face head** (`heads/face.py`):
  - YuNet finds faces of at least 64 px. Each face is aligned exactly as GenD's training data was, at the face's own scale.
  - **GenD** (default `yermandy/GenD_PE_L`) scores each face. A frame scores as its most suspicious face.
  - With no faces, the head reports `no_faces` and is unavailable, rather than voting "real".
- **Scene head** (`heads/scene.py`):
  - A linear probe on frozen CLIP ViT-L/14 features (**UnivFD**), applied to five 224 px crops per frame, taken at native resolution and never resized.
  - The bundled probe (`weights/univfd_fc.pth`) is UnivFD's original, trained on ProGAN images, so treat it as a baseline. Retraining it on modern video generators only means swapping that 768→1 layer (`SCENE_HEAD_WEIGHTS`).
- **Temporal head** (`heads/temporal.py`):
  - **D3**: the standard deviation of second-order differences between XCLIP-B/16 frame features, on 16-frame bursts at 8 fps. Low variation means AI.
  - The statistic has no built-in threshold. Until `D3_MIDPOINT` is set with `scripts/calibrate_d3.py`, the head reports the raw value with `reason: "uncalibrated"` and stays out of the verdict.
- **Fusion** (`aggregate.py`):
  - Each head's per-frame scores are averaged in logit space. The top-25% mean is reported as `peak`, to surface partial edits.
  - Heads that produced a probability are averaged in logit space.
  - Bands:
    - `likely_ai`: the fused score is at least 0.85, or one head is at least 0.95 across 3 or more frames. A confident face-swap hit is not averaged away by a scene head that has nothing to say about faces.
    - `no_evidence`: the fused score is at most 0.35, with no high peak and good input.
    - `inconclusive`: everything else.
  - `calibrated` stays false until the heads and the fuser are fitted on held-out data.

Hugging Face weights download into `weights/` on first start (about 4 GB), and only the 4 KB UnivFD probe is committed. Licences are listed in `weights/NOTICE.md`. Vendored GenD and UnivFD code sits under `app/vendor/`, with its MIT licences.

## Planned request flow

This is the target end-to-end flow. The steps marked ✗ in "Current state" below are not built yet.

1. The user signs in from the popup. The API returns a session token, which the extension keeps in `browser.storage`.
2. The user clicks Analyse. The content script captures N frames and streams them to the popup.
3. The popup sends the frames and video context (page URL, platform, duration, timestamps) to `POST /api/detections` with the bearer token.
4. The API:
   1. Authenticates the request and checks the user's quota.
   2. Hashes each frame and looks it up in `detection_cache`.
   3. Sends cache misses to the AI service.
   4. Aggregates frame scores into a video score.
   5. Writes `detection_results` and `frame_analyses` rows and increments usage.
5. The popup shows a calibrated probability, a confidence band and the strongest evidence (for example, the frames that scored highest), rather than a bare yes/no.
6. The user can flag the result as wrong. That writes to `reports` and feeds the evaluation set.

## Current state and gaps

Detection v1 works end to end in development: extension → AI service → result in the popup. What's left is routing it through the API, and calibration.

| Area | Status |
| --- | --- |
| Frame capture in the content script | ✓ Sparse frames and 8 fps bursts via canvas. ✓ Tab-capture fallback for tainted canvases (no bursts). ✗ DRM video still yields nothing |
| Popup state machine and UI | ✓ Calls the AI service and shows the verdict band, per-head scores and quality flags. ⚠ Calls the AI service directly instead of going through the API |
| Popup auth | ✗ `TabCards.vue` writes a fake token to `localStorage` and never calls the API. The user shown in `HomeView` is hard-coded |
| API auth routes | ✓ Sign-up and sign-in exist. ✗ No session middleware protects other routes yet |
| API detection routes | ✗ None. The API never calls the AI service |
| AI service heads | ✓ Face (GenD), scene (UnivFD) and temporal (D3), with pretrained weights. ✗ Nothing is calibrated on production-like data. ✗ The scene probe is trained on GAN images, not modern video generators. ✗ D3 has no threshold until it is calibrated |
| docker-compose | ⚠ There is no `api/Dockerfile` and no `init.sql`. It reserves an NVIDIA GPU, which does not work on macOS. The AI service image has not been rebuilt since the v1 changes |
| Tests | ✓ The AI service has unit tests for the quality gate, fusion, head maths and the endpoint, using stub heads. ✗ The extension and the API have none |

## Known constraints

These affect the design, not just the implementation.

- **Tainted canvases.** `drawImage` on a cross-origin video without CORS headers taints the canvas, and `toDataURL` then throws. Many hosts serve video through MSE/blob URLs, which work, but some players and all DRM (EME) content will never yield pixels. A fallback is `tabs.captureVisibleTab`, which screenshots the visible tab but also captures overlays and the page's own scaling.
- **Seeking changes the user's video.** Sparse capture seeks the player and then restores its position. On streaming sites, seeking can trigger buffering or ads. A seek that takes longer than 5 s just loses that frame.
- **Compression.** Frames have already been through the platform's re-encode and then our JPEG encode at quality 0.95. Detectors must be calibrated on frames that went through the same path.
- **Payload size.** A 1080p frame is about 300–500 KB as JPEG, so a full capture (up to 32 sparse frames plus 32 burst frames) is roughly 10–30 MB of base64. PNG would be about 6× larger. Frames are never resized beyond the 1920 px cap, because resampling destroys the artefacts the detectors look for.
- **Manifest V2.** Chrome no longer supports MV2. Shipping on Chrome needs an MV3 manifest, which replaces the background page with a service worker.
- **Privacy.** Frames can contain personal content. Store hashes and scores, not frames, unless the user opts in, for example by reporting a misclassification.

## Detection approach

Summary of [docs/ai-video-detection-research.md](docs/ai-video-detection-research.md):

No current detector generalises reliably to the latest commercial generators, so the product is a calibrated triage tool, not a verdict. The AI service runs independent heads, and each one reports its own score:

1. **Quality gate**: resolution, blur, black frames and shot boundaries. Poor input lowers the confidence ceiling.
2. **Face head**: face crops scored by **GenD** (MIT, pretrained weights), for face swaps and reenactment.
3. **Scene head**: full frames scored by a light head on frozen foundation-model features, for fully synthetic video where face models fail. v1 ships UnivFD's CLIP probe as a baseline. Retraining that probe on modern generated-video datasets is the main accuracy upgrade.
4. **Temporal head**: **D3** (MIT, training-free) on bursts of consecutive frames, for motion artefacts that single frames cannot show.
5. **Provenance and watermarks** (not in v1): open watermark decoders and visible-logo detection, reported separately. C2PA metadata does not survive frame capture. SynthID does, but it has no public verification API.
6. **Aggregate**:
   - Combine per-frame scores robustly (a top-k mean catches partial edits).
   - Fuse the heads.
   - Calibrate for a low false-positive rate.
   - Report **likely AI / inconclusive / no evidence found**, with the per-head evidence.

What this requires elsewhere in the system:

- **Extension (done):**
  - Captures sparse frames plus 8 fps bursts via `requestVideoFrameCallback`.
  - Uses high-quality JPEG at native resolution.
  - Tags each frame with its capture method and the rendition size.
- **API (to do):** store every head's output and the model versions in `detection_methods_used` and `provider_results`, so heads can be added or swapped without schema changes.
- **Training:** real and fake data go through the same encode → canvas → image path as production, and visible watermarks are masked so the model can't learn them as a shortcut.
