"""Scene head: a linear probe on frozen CLIP ViT-L/14 image features (UnivFD).

Scores whole frames, so it covers fully synthetic video where the face head has
nothing to say. Crops are taken at native resolution, never resized, because
resampling destroys the artefacts the probe relies on.

The bundled probe (weights/univfd_fc.pth) is UnivFD's original, trained on
ProGAN images. It is a baseline: swap in a probe trained on modern video
generators by pointing SCENE_HEAD_WEIGHTS at a new 768→1 linear layer.
"""

import numpy as np
import torch
from transformers import CLIPVisionModelWithProjection

from app.config import Settings
from app.pipeline.frames import Frame
from app.pipeline.heads.base import FrameScore, HeadResult, resolve_device, summarise

CROP = 224
CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(3, 1, 1)
CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(3, 1, 1)


def native_crops(rgb: np.ndarray, size: int = CROP) -> list[np.ndarray]:
    """Centre crop plus four crops centred on each quadrant, at native scale."""
    h, w = rgb.shape[:2]
    centres = [(0.5, 0.5), (0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]
    crops = []
    for cx, cy in centres:
        x = int(np.clip(cx * w - size / 2, 0, w - size))
        y = int(np.clip(cy * h - size / 2, 0, h - size))
        crops.append(rgb[y : y + size, x : x + size])
    return crops


def to_tensor(crop: np.ndarray) -> torch.Tensor:
    tensor = torch.from_numpy(crop.copy()).permute(2, 0, 1).float() / 255.0
    return (tensor - CLIP_MEAN) / CLIP_STD


class SceneHead:
    name = "scene"

    def __init__(self, settings: Settings):
        self.device = resolve_device(settings.device)
        self.model_name = f"univfd:{settings.scene_backbone}"
        self.backbone = CLIPVisionModelWithProjection.from_pretrained(
            settings.scene_backbone, cache_dir=settings.weights_dir
        )
        self.backbone.to(self.device).eval()

        self.probe = torch.nn.Linear(self.backbone.config.projection_dim, 1)
        state = torch.load(settings.scene_head_weights, map_location="cpu", weights_only=True)
        self.probe.load_state_dict(state)
        self.probe.to(self.device).eval()

    @torch.no_grad()
    def score(self, frames: list[Frame]) -> HeadResult:
        per_frame: list[FrameScore] = []
        for frame in frames:
            if min(frame.height, frame.width) < CROP:
                continue
            batch = torch.stack([to_tensor(c) for c in native_crops(frame.rgb)])
            features = self.backbone(pixel_values=batch.to(self.device)).image_embeds
            logits = self.probe(features).squeeze(-1)
            per_frame.append(
                FrameScore(frame.index, frame.timestamp, float(torch.sigmoid(logits.mean())))
            )

        if not per_frame:
            return HeadResult.unavailable(self.name, self.model_name, "frames_too_small")
        score, peak = summarise(per_frame)
        return HeadResult(
            name=self.name,
            model=self.model_name,
            available=True,
            score=score,
            peak=peak,
            frames_scored=len(per_frame),
            calibrated=False,
            per_frame=per_frame,
        )
