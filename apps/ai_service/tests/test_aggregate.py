import pytest

from app.config import Settings
from app.pipeline.aggregate import fuse
from app.pipeline.heads.base import FrameScore, HeadResult, summarise
from app.pipeline.quality import QualityReport
from tests.conftest import make_frame, textured

SETTINGS = Settings()


def good_quality() -> QualityReport:
    return QualityReport(usable_frames=[make_frame(textured(), i) for i in range(8)])


def head(name: str, score: float | None, peak: float | None = None, n: int = 8) -> HeadResult:
    return HeadResult(
        name=name, model="m", available=True, score=score, peak=peak or score, frames_scored=n
    )


def test_summarise_score_and_peak():
    frames = [FrameScore(i, None, s) for i, s in enumerate([0.1, 0.1, 0.1, 0.9])]
    score, peak = summarise(frames)
    assert score < 0.5
    assert peak == pytest.approx(0.9)


def test_no_scored_heads_is_inconclusive():
    fused = fuse([HeadResult.unavailable("face", "m", "no_faces")], good_quality(), SETTINGS)
    assert fused.verdict == "inconclusive"
    assert fused.probability is None


def test_uncalibrated_head_is_ignored():
    fused = fuse([head("scene", 0.1), head("temporal", None)], good_quality(), SETTINGS)
    assert fused.verdict == "no_evidence"


def test_all_heads_low_is_no_evidence():
    fused = fuse([head("face", 0.1), head("scene", 0.2)], good_quality(), SETTINGS)
    assert fused.verdict == "no_evidence"


def test_all_heads_high_is_likely_ai():
    fused = fuse([head("face", 0.9), head("scene", 0.9)], good_quality(), SETTINGS)
    assert fused.verdict == "likely_ai"


def test_one_confident_head_is_not_averaged_away():
    fused = fuse([head("face", 0.98), head("scene", 0.1)], good_quality(), SETTINGS)
    assert fused.verdict == "likely_ai"
    assert fused.reasons == ["face_head_confident"]


def test_confident_head_on_too_few_frames_is_only_inconclusive():
    fused = fuse([head("face", 0.98, n=1), head("scene", 0.1)], good_quality(), SETTINGS)
    assert fused.verdict == "inconclusive"


def test_high_peak_blocks_no_evidence():
    fused = fuse([head("face", 0.1, peak=0.9), head("scene", 0.1)], good_quality(), SETTINGS)
    assert fused.verdict == "inconclusive"
    assert "face_head_peak_high" in fused.reasons


def test_poor_quality_blocks_no_evidence():
    fused = fuse([head("scene", 0.1)], QualityReport(), SETTINGS)
    assert fused.verdict == "inconclusive"
    assert "input_quality_poor" in fused.reasons
