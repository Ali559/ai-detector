"""Temporal head: D3 (Zheng et al., ICCV 2025), training-free.

Encodes each frame of a burst, takes the L2 distance between consecutive
features (first order), then the change in that distance (second order). Real
footage has irregular second-order motion; generated video tends to be
smoother, so a LOW standard deviation points to AI.

Matches the reference setup (https://github.com/Zig-HS/D3): 16 frames sampled
at 8 fps, resized to 224x224, ImageNet normalisation, XCLIP-B/16 pooled
features, L2 distance.

The statistic has no natural threshold, so this head only reports it
(`details.d3_std`). calibration.json (tools/calibrate.py) maps it to a
probability; until then the head stays out of the fused score.
"""

import numpy as np
import torch
import torch.nn.functional as F

from app.config import Settings
from app.pipeline.frames import Frame
from app.pipeline.heads.base import HeadResult, resolve_device

REFERENCE_FPS = 8.0
BURST_LENGTHS = (16, 8)  # XCLIP's cross-frame attention groups frames in eights
SIZE = 224
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
IMAGENET_STD = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)


def second_order_std(features: torch.Tensor) -> float:
    """D3 statistic for one burst of features, shape (T, D)."""
    first = torch.norm(features[1:] - features[:-1], p=2, dim=-1)
    second = first[1:] - first[:-1]
    return float(torch.std(second))


def trim_burst(burst: list[Frame]) -> list[Frame] | None:
    for length in BURST_LENGTHS:
        if len(burst) >= length:
            start = (len(burst) - length) // 2
            return burst[start : start + length]
    return None


def burst_tensor(burst: list[Frame]) -> torch.Tensor:
    stack = np.stack([f.rgb for f in burst])
    tensor = torch.from_numpy(stack).permute(0, 3, 1, 2).float() / 255.0
    tensor = F.interpolate(tensor, size=(SIZE, SIZE), mode="bilinear", antialias=True)
    return (tensor - IMAGENET_MEAN) / IMAGENET_STD


class TemporalHead:
    name = "temporal"

    def __init__(self, settings: Settings):
        from transformers import XCLIPVisionModel

        self.settings = settings
        self.device = resolve_device(settings.device)
        self.model_name = f"d3:{settings.temporal_encoder}"
        self.encoder = XCLIPVisionModel.from_pretrained(
            settings.temporal_encoder, cache_dir=settings.weights_dir
        )
        self.encoder.to(self.device).eval()

    @torch.no_grad()
    def statistic(self, burst: list[Frame]) -> float:
        pixels = burst_tensor(burst).to(self.device)
        features = self.encoder(pixel_values=pixels).pooler_output
        return second_order_std(features.float().cpu())

    def score(self, bursts: list[tuple[float, list[Frame]]]) -> HeadResult:
        stats: list[float] = []
        frames_used = 0
        off_rate = False
        for fps, burst in bursts:
            trimmed = trim_burst(burst)
            if trimmed is None:
                continue
            off_rate = off_rate or abs(fps - REFERENCE_FPS) > 1.0
            stats.append(self.statistic(trimmed))
            frames_used += len(trimmed)

        if not stats:
            return HeadResult.unavailable(self.name, self.model_name, "no_usable_bursts")

        # The least volatile burst is the most suspicious one.
        raw = min(stats)
        details: dict = {"d3_std": raw, "d3_std_per_burst": stats, "bursts_scored": len(stats)}
        if off_rate:
            details["warning"] = f"bursts not captured at {REFERENCE_FPS:g} fps"
        return HeadResult(
            name=self.name,
            model=self.model_name,
            available=True,
            frames_scored=frames_used,
            reason="uncalibrated",
            details=details,
        )
