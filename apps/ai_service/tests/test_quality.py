import numpy as np

from app.pipeline.quality import assess, burst_issue, frame_issue
from tests.conftest import make_frame, pan, textured


def test_textured_frame_is_usable():
    assert frame_issue(make_frame(textured())) is None


def test_blank_and_tiny_frames_are_rejected():
    assert frame_issue(make_frame(np.zeros((480, 640, 3), np.uint8))) == "blank"
    assert frame_issue(make_frame(textured(100, 120))) == "too_small"


def test_burst_with_motion_is_usable():
    burst = [make_frame(f, i) for i, f in enumerate(pan(textured()))]
    assert burst_issue(burst) is None


def test_static_burst_is_rejected():
    still = textured()
    assert burst_issue([make_frame(still, i) for i in range(16)]) == "static"


def test_burst_with_scene_cut_is_rejected():
    frames = pan(textured(seed=1), 8) + [255 - f for f in pan(textured(seed=2), 8)]
    assert burst_issue([make_frame(f, i) for i, f in enumerate(frames)]) == "scene_cut"


def test_assess_flags_low_resolution_and_screen_capture():
    frames = [make_frame(textured(240, 320, seed=i), i) for i in range(5)]
    report = assess(frames, [], capture_method="tab_capture")
    assert len(report.usable_frames) == 5
    assert "low_resolution" in report.flags
    assert "screen_capture" in report.flags
    assert report.poor


def test_assess_falls_back_to_burst_frames():
    burst = [make_frame(f, i) for i, f in enumerate(pan(textured()))]
    report = assess([], [burst])
    assert report.usable_frames == [burst[8]]
    assert "frames_from_bursts" in report.flags
