"""Calibration fitted by tools/calibrate.py, stored as calibration.json.

Without a calibration file the service still works: face and scene scores are
the models' raw outputs, D3 stays out of the verdict, heads are averaged, and
the verdict bands come from the environment. With one:

- each head's score is Platt-scaled: p = sigmoid(a * x + b), where x is the
  head's raw logit (face, scene) or the raw D3 statistic (temporal);
- heads are fused by a fitted logistic regression on their calibrated logits
  (a head that couldn't score contributes 0, i.e. no evidence either way);
- the verdict thresholds are the ones chosen for the target error rates.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.pipeline.heads.base import HeadResult, logit, sigmoid

VERSION = 1


@dataclass
class Platt:
    a: float
    b: float

    def __call__(self, x: float) -> float:
        return sigmoid(self.a * x + self.b)


@dataclass
class Calibration:
    heads: dict[str, Platt]
    fuser_weights: dict[str, float]
    fuser_bias: float
    likely_ai_threshold: float
    no_evidence_threshold: float
    metrics: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Calibration":
        data = json.loads(path.read_text())
        if data.get("version") != VERSION:
            raise ValueError(f"{path}: unsupported calibration version {data.get('version')}")
        return cls(
            heads={name: Platt(**p) for name, p in data["heads"].items()},
            fuser_weights=data["fuser"]["weights"],
            fuser_bias=data["fuser"]["bias"],
            likely_ai_threshold=data["thresholds"]["likely_ai"],
            no_evidence_threshold=data["thresholds"]["no_evidence"],
            metrics=data.get("metrics", {}),
        )

    def to_json(self) -> dict:
        return {
            "version": VERSION,
            "heads": {name: {"a": p.a, "b": p.b} for name, p in self.heads.items()},
            "fuser": {"weights": self.fuser_weights, "bias": self.fuser_bias},
            "thresholds": {
                "likely_ai": self.likely_ai_threshold,
                "no_evidence": self.no_evidence_threshold,
            },
            "metrics": self.metrics,
        }

    def apply(self, result: HeadResult) -> HeadResult:
        """Replace a head's raw scores with calibrated ones, in place."""
        platt = self.heads.get(result.name)
        if platt is None or not result.available:
            return result
        if result.name == "temporal":
            raw = result.details.get("d3_std")
            if raw is None:
                return result
            result.score = result.peak = platt(raw)
            result.reason = None
        else:
            if result.score is None:
                return result
            result.score = platt(logit(result.score))
            if result.peak is not None:
                result.peak = platt(logit(result.peak))
            for frame in result.per_frame:
                frame.score = platt(logit(frame.score))
        result.calibrated = True
        return result

    def fuse(self, results: list[HeadResult]) -> float | None:
        scored = [r for r in results if r.available and r.score is not None]
        if not scored:
            return None
        z = self.fuser_bias + sum(
            self.fuser_weights.get(r.name, 0.0) * logit(r.score) for r in scored
        )
        return sigmoid(z)
