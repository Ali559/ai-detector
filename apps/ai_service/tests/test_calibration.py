import json

import pytest

from app.config import Settings
from app.pipeline.aggregate import fuse
from app.pipeline.calibration import Calibration, Platt
from app.pipeline.heads.base import FrameScore, HeadResult, logit
from app.pipeline.quality import QualityReport
from tests.conftest import make_frame, textured


def calibration(**overrides) -> Calibration:
    values = dict(
        heads={"face": Platt(1.0, 0.0), "scene": Platt(2.0, -1.0), "temporal": Platt(-10.0, 20.0)},
        fuser_weights={"face": 1.0, "scene": 0.5, "temporal": 1.0},
        fuser_bias=-0.5,
        likely_ai_threshold=0.7,
        no_evidence_threshold=0.3,
    )
    values.update(overrides)
    return Calibration(**values)


def good_quality() -> QualityReport:
    return QualityReport(usable_frames=[make_frame(textured(), i) for i in range(8)])


def test_platt_is_monotonic_sigmoid():
    p = Platt(2.0, -1.0)
    assert p(0.5) == pytest.approx(0.5)
    assert p(1.0) > p(0.0)


def test_apply_rescales_probability_heads_and_frames():
    head = HeadResult(
        "scene", "m", True, score=0.5, peak=0.5, frames_scored=1,
        per_frame=[FrameScore(0, None, 0.5)],
    )
    calibration().apply(head)
    expected = Platt(2.0, -1.0)(logit(0.5))
    assert head.score == pytest.approx(expected)
    assert head.per_frame[0].score == pytest.approx(expected)
    assert head.calibrated


def test_apply_turns_d3_statistic_into_probability():
    head = HeadResult("temporal", "m", True, reason="uncalibrated", details={"d3_std": 1.5})
    calibration().apply(head)
    # Low volatility (1.5 < 2.0 midpoint) means AI.
    assert head.score == pytest.approx(Platt(-10.0, 20.0)(1.5))
    assert head.score > 0.99
    assert head.reason is None and head.calibrated


def test_apply_leaves_uncalibrated_heads_alone():
    head = HeadResult("face", "m", True, score=0.8, peak=0.8, frames_scored=3)
    calibration(heads={}).apply(head)
    assert head.score == 0.8 and not head.calibrated


def test_fuse_uses_fitted_weights_and_thresholds():
    cal = calibration()
    heads = [HeadResult("face", "m", True, score=0.6, peak=0.6, frames_scored=8)]
    fused = fuse(heads, good_quality(), Settings(), cal)
    assert fused.probability == pytest.approx(cal.fuse(heads))
    assert fused.verdict == "inconclusive"  # 0.52 sits between 0.3 and 0.7


def test_round_trip(tmp_path):
    cal = calibration(metrics={"fused_auc": 0.9})
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps(cal.to_json()))
    loaded = Calibration.load(path)
    assert loaded.heads["scene"] == cal.heads["scene"]
    assert loaded.fuser_weights == cal.fuser_weights
    assert loaded.metrics == {"fused_auc": 0.9}
