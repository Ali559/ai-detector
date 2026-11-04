"""Fuse head results into one verdict.

With calibration.json, heads are combined by the fitted fuser and the bands
use the fitted thresholds. Without it, heads are averaged in logit space with
conservative bands from the environment, so a real video is rarely called fake:

- likely_ai:    fused >= LIKELY_AI_THRESHOLD, or one head is near-certain
                (>= 0.95) over enough frames. Different heads catch different
                fakes, so a confident face-swap hit shouldn't be averaged away
                by a scene head that has nothing to say about faces.
- no_evidence:  fused <= NO_EVIDENCE_THRESHOLD, no head above the likely-AI
                threshold even at its peak, and the input was good enough to
                look at.
- inconclusive: everything else, including when no head could score.
"""

from dataclasses import dataclass
from typing import Literal

from app.config import Settings
from app.pipeline.calibration import Calibration
from app.pipeline.heads.base import HeadResult, logit, sigmoid
from app.pipeline.quality import QualityReport

Verdict = Literal["likely_ai", "inconclusive", "no_evidence"]


@dataclass
class Fused:
    verdict: Verdict
    probability: float | None
    reasons: list[str]


def fuse(
    heads: list[HeadResult],
    quality: QualityReport,
    settings: Settings,
    calibration: Calibration | None = None,
) -> Fused:
    scored = [h for h in heads if h.available and h.score is not None]
    if not scored:
        return Fused("inconclusive", None, ["no_head_could_score"])

    if calibration is not None:
        probability = calibration.fuse(scored)
        likely_ai = calibration.likely_ai_threshold
        no_evidence = calibration.no_evidence_threshold
    else:
        probability = sigmoid(sum(logit(h.score) for h in scored) / len(scored))
        likely_ai = settings.likely_ai_threshold
        no_evidence = settings.no_evidence_threshold
    reasons: list[str] = []

    strong = [
        h.name
        for h in scored
        if h.score >= settings.strong_head_threshold
        and h.frames_scored >= settings.strong_head_min_frames
    ]
    if probability >= likely_ai:
        return Fused("likely_ai", probability, ["fused_score_high"])
    if strong:
        return Fused("likely_ai", probability, [f"{name}_head_confident" for name in strong])

    peaked = [h.name for h in scored if (h.peak or 0) >= likely_ai]
    if peaked:
        reasons += [f"{name}_head_peak_high" for name in peaked]
    if quality.poor:
        reasons.append("input_quality_poor")

    if probability <= no_evidence and not reasons:
        return Fused("no_evidence", probability, ["fused_score_low"])
    if not reasons:
        reasons.append("fused_score_in_middle_band")
    return Fused("inconclusive", probability, reasons)
