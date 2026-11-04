"""Scene head: a linear probe on frozen CLIP ViT-L/14 image features (UnivFD).

Scores whole frames, so it covers fully synthetic video where the face head has
nothing to say. Crops are taken at native resolution, never resized, because
resampling destroys the artefacts the probe relies on.

Crops stay inside the central 80% of the frame where possible, so corner
watermarks (Sora, Veo, Kling logos) don't become a shortcut the probe learns.

The bundled probe (weights/univfd_fc.pth) is UnivFD's original, trained on
ProGAN images. It is a baseline: training/ fits a replacement on modern video
generators, loaded by pointing SCENE_HEAD_WEIGHTS at the new 768→1 layer.
"""

import numpy as np
import torch
from transformers import CLIPVisionModelWithProjection

from app.config import Settings
from app.pipeline.frames import Frame
from app.pipeline.heads.base import FrameScore, HeadResult, resolve_device, summarise

CROP = 224
MARGIN = 0.1  # fraction of each side kept out of crops when the frame allows
CLIP_MEAN = torch.tensor([0.48145466, 0.4578275, 0.40821073]).view(3, 1, 1)
CLIP_STD = torch.tensor([0.26862954, 0.26130258, 0.27577711]).view(3, 1, 1)


def _span(length: int, size: int) -> tuple[int, int]:
    """Allowed range for a crop's start along one axis."""
    margin = int(length * MARGIN)
    if length - 2 * margin >= size:
        return margin, length - margin - size
    return 0, length - size


def native_crops(rgb: np.ndarray, size: int = CROP) -> list[np.ndarray]:
    """Centre crop plus four crops towards each quadrant, at native scale."""
    h, w = rgb.shape[:2]
    x_lo, x_hi = _span(w, size)
    y_lo, y_hi = _span(h, size)
    centres = [(0.5, 0.5), (0.3, 0.3), (0.7, 0.3), (0.3, 0.7), (0.7, 0.7)]
    crops = []
    for cx, cy in centres:
        x = int(np.clip(cx * w - size / 2, x_lo, x_hi))
        y = int(np.clip(cy * h - size / 2, y_lo, y_hi))
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
    def features(self, frame: Frame) -> torch.Tensor | None:
        """CLIP image embeddings of the frame's crops, shape (5, 768), or None
        if the frame is too small. Shared with training/extract_features.py."""
        if min(frame.height, frame.width) < CROP:
            return None
        batch = torch.stack([to_tensor(c) for c in native_crops(frame.rgb)])
        return self.backbone(pixel_values=batch.to(self.device)).image_embeds

    @torch.no_grad()
    def score(self, frames: list[Frame]) -> HeadResult:
        per_frame: list[FrameScore] = []
        for frame in frames:
            features = self.features(frame)
            if features is None:
                continue
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
