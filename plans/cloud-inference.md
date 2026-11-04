# Plan: rent cloud GPUs for testing

**Goal:** run the full system (extension → API → AI service on a GPU) for a few hours a week, from anywhere, paying close to nothing while idle.

**Recommendation:** run the AI service on **Modal** with an L4 GPU that scales to zero. Modal's $30/month free credit should cover testing. Keep the API local, or put it on any small free host. The fallback is a **RunPod Community Cloud** pod at about $0.16–0.22/hour that you start and stop by hand.

Prices were checked on 4 Nov 2026 from providers' pricing pages. They change, so confirm in the console before renting. Sources are at the end.

## What the workload needs

- **Three models in memory:** GenD-PE-L, CLIP ViT-L/14 and XCLIP-B/16, about 3 GB of weights. Any GPU with 16 GB or more is plenty; 24 GB is comfortable.
- **Per request:** about 100–200 ViT forward passes. Expect about 0.5–2 s on an L4 or RTX 3090. On a 16-vCPU machine it's about 20–40 s, and 40–90 s on 8 vCPU (these CPU figures are estimates, not benchmarks).
- **Payload:** 10–30 MB of JPEG frames per request.
- **Disk:** about 4 GB for weights, plus about 6 GB for the Python environment.

**A CPU-only server is not worth it.** A 16-vCPU Hetzner box costs about the same per hour as a community RTX 3090, which is 20–50× faster. Use CPU only to check that things run, never for interactive use.

## Option A (recommended): Modal, serverless L4

| | |
| --- | --- |
| Price | L4 about $0.80/hr for the GPU, plus about $0.30/hr for CPU and RAM, billed per second |
| Idle cost | $0. The container shuts down 5 minutes after the last request (`SCALEDOWN_SECONDS` in the deploy file) |
| Cold start | About 1 s to boot the container, plus about 10–30 s to load the models from the cached Volume. The first request of a session is slow; the rest are fast |
| Storage | Volume at $0.09/GiB/month; about 10 GB is likely covered by the free allowance |
| HTTPS | Stable `https://<workspace>--ai-detector-web.modal.run` URL, out of the box |
| Free tier | Starter plan includes **$30/month of credit**, recurring |

The deploy file is [`apps/ai_service/deploy/modal_app.py`](../apps/ai_service/deploy/modal_app.py). The FastAPI app runs unchanged.

```bash
cd apps/ai_service
pip install modal && modal setup
modal secret create ai-detector SERVICE_TOKEN=$(openssl rand -hex 32)
modal run deploy/modal_app.py::download_weights
modal deploy deploy/modal_app.py
```

Then set these on the API:

- `AI_SERVICE_URL`: the printed `modal.run` URL.
- `AI_SERVICE_TOKEN`: the same token you put in the secret.

To stop all billing, run `modal app stop ai-detector`.

**Cost at 10 hours a week of testing:**

- About 43 hours a month, of which roughly half is spent warm. That's about 21 GPU-hours × $1.12 ≈ **$24**, inside the $30 credit.
- Worst case, if the container is warm the whole time: about $48, so **about $18 net**.

## Option B (fallback): RunPod Community Cloud pod

| | |
| --- | --- |
| Price | RTX A5000 24 GB **$0.16/hr**, RTX 3090 **$0.22/hr**, RTX 4090 $0.34/hr. Secure Cloud costs about 2–3× more but is more reliable |
| Idle cost | Stop the pod when you're done. A 10 GB network volume costs **$0.70/month** and keeps the venv and weights |
| HTTPS | `https://<pod-id>-8000.proxy.runpod.net`. **Requests are capped at 100 s**, which is fine at about 2–10 s per request |
| Egress | Free |

Setup script: [`apps/ai_service/deploy/runpod_setup.sh`](../apps/ai_service/deploy/runpod_setup.sh).

1. Create a 10 GB network volume.
2. Start a PyTorch-template pod on a Community A5000 or 3090, with the volume at `/workspace` and HTTP port 8000 exposed.
3. Run:

   ```bash
   export SERVICE_TOKEN=<your token>
   bash deploy/runpod_setup.sh
   ```

The first run takes about 10 minutes to download weights; later starts take about 1 minute. **Stop the pod as soon as you've finished testing.** A forgotten 3090 costs about $160 a month.

**Cost at 10 hours a week:** 43 h × $0.22 + $0.70 ≈ **$10/month**, or about $8 on an A5000.

## Option C: your own machine plus a tunnel ($0)

You can run the service on your Mac (it works, with the face model on CPU) and expose it with `cloudflared tunnel --url http://localhost:8000`. That gives a free HTTPS URL that changes on every run. It's good for showing someone a demo, but the result is only as fast as your laptop.

## Don't use these

| Option | Why not |
| --- | --- |
| Replicate | Private models are billed for setup and idle time, and you'd have to repackage the app with Cog |
| Paperspace | Billed by the hour, and expensive |
| HF Inference Endpoints | Scales to zero only after 15 minutes idle, and returns 502 while warming up. That works out to about $40/month for the same usage |
| HF ZeroGPU | Free, but runs Gradio apps only, not this FastAPI service |
| Colab | Free runtimes forbid serving web apps |
| RunPod Serverless | Workable, but $0.75/hr on a 24 GB card, a 30 MB payload cap (our largest requests come close), and no request queue |

## Security checklist before exposing anything

- [ ] `SERVICE_TOKEN` is set on the AI service. Without it, anyone who finds the URL can use your GPU. The service rejects unauthenticated `/analyze/video` calls once it's set.
- [ ] The API has `AI_SERVICE_TOKEN` set to the same value. Never put that token in the extension: the extension talks to the API, and only the API talks to the AI service.
- [ ] A spending limit is set in the provider's console. Modal and RunPod both support one.
- [ ] Pods are stopped after testing. Put a reminder in your calendar.

## Monthly budget

At 10 hours of testing a week:

| Setup | Monthly |
| --- | --- |
| Modal L4, AI service only | **$0–18** (within the free credit at typical use) |
| RunPod Community A5000/3090 pod | **$8–11** |
| Your Mac plus a tunnel | **$0** (slow) |

Training compute is planned separately in [training.md](training.md).

## Sources

- RunPod pricing and pod docs: https://www.runpod.io/pricing · https://docs.runpod.io/pods/pricing · https://docs.runpod.io/pods/configuration/expose-ports · https://docs.runpod.io/serverless/load-balancing/overview
- Modal pricing, cold starts and web endpoints: https://modal.com/pricing · https://modal.com/docs/guide/cold-start · https://modal.com/docs/guide/webhooks
- Hugging Face Endpoints pricing and autoscaling, and ZeroGPU: https://huggingface.co/docs/inference-endpoints/support/pricing · https://huggingface.co/docs/inference-endpoints/autoscaling · https://huggingface.co/docs/hub/spaces-zerogpu
- Replicate: https://replicate.com/pricing
- Paperspace: https://www.paperspace.com/pricing
- Colab FAQ: https://research.google.com/colaboratory/faq.html
- Cloudflare quick tunnels: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
- **Unverified (third-party sources only):** Vast.ai, TensorDock and AWS/GCP spot prices; Hetzner prices after the 2026 increase. The CPU latency figures are estimates from FLOP counts, not measurements.
