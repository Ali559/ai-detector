#!/usr/bin/env bash
# Set up and start the AI service on a RunPod GPU pod (or any Linux GPU box).
#
# Use a PyTorch template pod with a network volume mounted at /workspace, so
# the venv and the ~4 GB of weights survive stopping the pod. Pay only while
# the pod runs; stop it when you're done (see plans/cloud-inference.md).
#
#   export SERVICE_TOKEN=$(openssl rand -hex 32)   # keep it; the API needs it
#   bash deploy/runpod_setup.sh
#
# Expose HTTP port 8000 in the pod settings. RunPod then serves it at
# https://<pod-id>-8000.proxy.runpod.net (requests are capped at 100 s).
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/Ali559/ai-detector.git}"
WORKSPACE="${WORKSPACE:-/workspace}"
SERVICE_DIR="$WORKSPACE/ai-detector/apps/ai_service"

if [ -z "${SERVICE_TOKEN:-}" ]; then
  echo "Set SERVICE_TOKEN first: anyone with the URL could use your GPU otherwise." >&2
  exit 1
fi

command -v ffmpeg >/dev/null || (apt-get update -qq && apt-get install -y -qq ffmpeg)
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

if [ -d "$WORKSPACE/ai-detector/.git" ]; then
  git -C "$WORKSPACE/ai-detector" pull --ff-only
else
  git clone --depth 1 "$REPO_URL" "$WORKSPACE/ai-detector"
fi

cd "$SERVICE_DIR"
[ -d .venv ] || uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -q -r requirements.txt

# Keep every model download on the network volume.
export WEIGHTS_DIR="$WORKSPACE/weights"
export HF_HOME="$WORKSPACE/weights/hf"
mkdir -p "$WEIGHTS_DIR"

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
