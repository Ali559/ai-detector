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
  1. Finds all `<video>` elements, including inside shadow roots.
  2. Picks the first one that is playing and has decoded data.
  3. Seeks forward through up to 30 s of the remaining video, at intervals of at least 0.5 s, and draws each frame to a canvas sized to the video's native resolution.
  4. Encodes each frame as JPEG (quality 0.8), drops duplicates by SHA-256, and streams each one back as an `extracted` message.
  5. Sends `extraction-completed`, then restores the original playback position.
- **Background script**: `src/background/background.ts`. Relays `start` from the popup to the active tab's content script.
- **Popup**: `src/popup/App.vue` plus `src/Views/*`. A Vue app with a hash router and Pinia.
  - `AuthView` holds the login and signup tabs.
  - `HomeView` and `MainContent.vue` drive a small state machine: `idle → extracting → extracted → analyzing → completed`. Each state has its own card component in `src/components/molecules/Home/`.

### Message protocol

Messages are defined in `src/types/index.ts` (`ResponseType`, `IVideoFrame`, `IExtractionResponse`).

| Message | From → To | Payload |
| --- | --- | --- |
| `start` | popup → background → content | `frameCount` |
| `extracted` | content → popup | `videoId`, `data: IVideoFrame` (base64 JPEG, size, timestamp, duration, frame number) |
| `extraction-completed` | content → popup | `videoId`, `frameCount` |
| `error` | any → popup | `error` string |

`analyse` and `analysed` are reserved for the analysis round trip.

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

A FastAPI app (`app/main.py`). On startup, its lifespan hook loads the model through `InferenceService` (`app/services/inference.py`), which picks CUDA, then MPS, then CPU, and uses FP16 on CUDA.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Liveness, and whether the model is loaded |
| `POST /analyze` | One image (multipart or base64) → `AnalyzeResponse` |
| `POST /analyze/batch` | Several images → a list of `AnalyzeResponse` |

`AnalyzeResponse` (`app/schemas.py`) contains `ai_score` (0–1), `is_flagged` (threshold 0.7), a 768-d `embedding`, `phash`, `sha256` and `inference_time_ms`.

- **Model** (`app/models/deepfake_detector.py`): an EfficientNet-B0 backbone pretrained on ImageNet, followed by a 768-d embedding layer and an MLP head with sigmoid output. `CLIPBasedDetector` is a stub for an alternative backbone.
- **Preprocessing** (`app/services/image_processing.py`): resizes to 224×224 with ImageNet normalisation.
- **Hashing** (`app/utils/hashing.py`): SHA-256 plus perceptual hashes (pHash, dHash, aHash), for caching and near-duplicate lookup.

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

The pipeline currently ends after frame capture. Everything after that is mocked or missing.

| Area | Status |
| --- | --- |
| Frame capture in the content script | ✓ Works on playing, same-origin or CORS-enabled videos |
| Popup state machine and UI | ✓ UI exists. ✗ The analysis progress bar is a timer, and the result in `AnalysisCompleteCard.vue` is hard-coded (`isAI: false, confidence: 75`) |
| Popup auth | ✗ `TabCards.vue` writes a fake token to `localStorage` and never calls the API. The user shown in `HomeView` is hard-coded |
| API auth routes | ✓ Sign-up and sign-in exist. ✗ No session middleware protects other routes yet |
| API detection routes | ✗ None. The API never calls the AI service |
| AI service model | ✗ There are no trained weights. If `MODEL_PATH` is missing, the service falls back to an ImageNet backbone with an untrained head, so `ai_score` means nothing |
| AI service `/analyze` | ⚠ Mixes an optional `UploadFile` with a JSON body model, which FastAPI does not support in one route |
| docker-compose | ⚠ Points at `ai_service/.Dockerfile`, but the file is `Dockerfile`. There is no `api/Dockerfile` and no `init.sql`. It reserves an NVIDIA GPU, which does not work on macOS |
| Tests | ✗ The extension has no unit tests, the API has none, and the AI service has `tests/test_api.py` |

## Known constraints

These affect the design, not just the implementation.

- **Tainted canvases.** `drawImage` on a cross-origin video without CORS headers taints the canvas, and `toDataURL` then throws. Many hosts serve video through MSE/blob URLs, which work, but some players and all DRM (EME) content will never yield pixels. A fallback is `tabs.captureVisibleTab`, which screenshots the visible tab but also captures overlays and the page's own scaling.
- **Seeking changes the user's video.** The capture loop seeks the player and then restores its position. On streaming sites, seeking can trigger buffering or ads. A gentler mode would capture frames at natural playback time using `requestVideoFrameCallback`.
- **Temporal signal.** Frames 0.5 s or more apart are good for frame-level classifiers but discard the frame-to-frame motion that video-level detectors rely on. The research doc recommends also capturing short bursts of consecutive frames.
- **Compression.** Frames have already been through the platform's re-encode and then through our own JPEG encode at quality 0.8. Detectors must be trained and evaluated on frames with similar compression. A lossless (PNG) or high-quality capture option avoids adding another round of artefacts.
- **Payload size.** Full-resolution base64 JPEGs are large. Resize or crop on the client before upload, but only in ways the model was trained to expect.
- **Manifest V2.** Chrome no longer supports MV2. Shipping on Chrome needs an MV3 manifest, which replaces the background page with a service worker.
- **Privacy.** Frames can contain personal content. Store hashes and scores, not frames, unless the user opts in, for example by reporting a misclassification.

## Detection approach

Summary of [docs/ai-video-detection-research.md](docs/ai-video-detection-research.md):

No current detector generalises reliably to the latest commercial generators, so the product is a calibrated triage tool, not a verdict. The AI service runs independent heads, and each one reports its own score:

1. **Quality gate**: resolution, blur, black frames and shot boundaries. Poor input lowers the confidence ceiling.
2. **Face head**: face crops scored by **GenD** (MIT, pretrained weights), for face swaps and reenactment.
3. **Scene head**: full frames scored by a light head on frozen CLIP, DINOv3 or Perception Encoder features, trained on modern generated-video datasets. This head catches fully synthetic video, where face models fail.
4. **Temporal head**: **D3** (MIT, training-free) on bursts of consecutive frames, for motion artefacts that single frames cannot show.
5. **Provenance and watermarks**: open watermark decoders and visible-logo detection, reported separately. C2PA metadata does not survive frame capture. SynthID does, but it has no public verification API.
6. **Aggregate**:
   - Combine per-frame scores robustly (a top-k mean catches partial edits).
   - Fuse the heads.
   - Calibrate for a low false-positive rate.
   - Report **likely AI / inconclusive / no evidence found**, with the per-head evidence.

What this requires elsewhere in the system:

- **Extension:**
  - Capture 16–32 sparse frames plus short bursts of consecutive frames via `requestVideoFrameCallback`.
  - Use PNG or high-quality JPEG at native resolution.
  - Record the capture method and the rendition size with each frame.
- **API:** store every head's output and the model versions in `detection_methods_used` and `provider_results`, so heads can be added or swapped without schema changes.
- **Training:** real and fake data go through the same encode → canvas → image path as production, and visible watermarks are masked so the model can't learn them as a shortcut.
