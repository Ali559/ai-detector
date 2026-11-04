import math
from dataclasses import dataclass, field
from typing import Any

import torch


@dataclass
class FrameScore:
    index: int
    timestamp: float | None
    score: float  # probability the frame is AI-generated or manipulated
    faces: int | None = None


@dataclass
class HeadResult:
    """One detector's verdict. `score` is a probability in [0, 1], or None when
    the head ran but has no calibrated mapping to a probability."""

    name: str
    model: str
    available: bool
    score: float | None = None
    peak: float | None = None
    frames_scored: int = 0
    calibrated: bool = False
    reason: str | None = None
    per_frame: list[FrameScore] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def unavailable(cls, name: str, model: str, reason: str) -> "HeadResult":
        return cls(name=name, model=model, available=False, reason=reason)


def logit(p: float, eps: float = 1e-6) -> float:
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def summarise(per_frame: list[FrameScore]) -> tuple[float, float]:
    """Return (score, peak) for a head from its per-frame probabilities.

    score: mean in logit space, so a few confident frames don't swamp it.
    peak: mean of the top 25% of frames, to surface partial edits without
    letting them drive the verdict on their own.
    """
    logits = sorted((logit(f.score) for f in per_frame), reverse=True)
    k = max(1, math.ceil(len(logits) * 0.25))
    return sigmoid(sum(logits) / len(logits)), sigmoid(sum(logits[:k]) / k)


def resolve_device(preference: str) -> torch.device:
    if preference != "auto":
        return torch.device(preference)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
