"""Input-quality gate.

Detectors are unreliable on tiny, blank, blurry or screen-captured frames, and
D3 is meaningless on bursts that contain a scene cut or no motion at all. This
module decides which frames and bursts the heads may use, and flags input that
should lower our confidence.
"""

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.pipeline.frames import Frame

MIN_USABLE_SIDE = 144
LOW_RES_SIDE = 360
BLANK_STD = 6.0
BLUR_VARIANCE = 15.0
CUT_DIFF = 40.0
STATIC_DIFF = 0.5
MIN_USABLE_FRAMES = 4


@dataclass
class QualityReport:
    usable_frames: list[Frame] = field(default_factory=list)
    usable_bursts: list[list[Frame]] = field(default_factory=list)
    total_frames: int = 0
    flags: list[str] = field(default_factory=list)

    @property
    def poor(self) -> bool:
        return (
            len(self.usable_frames) < MIN_USABLE_FRAMES
            or "low_resolution" in self.flags
            or "screen_capture" in self.flags
        )

    def flag(self, name: str) -> None:
        if name not in self.flags:
            self.flags.append(name)


def _gray(frame: Frame, max_side: int = 512) -> np.ndarray:
    gray = cv2.cvtColor(frame.rgb, cv2.COLOR_RGB2GRAY)
    scale = max_side / max(gray.shape)
    if scale < 1:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return gray


def frame_issue(frame: Frame) -> str | None:
    """Return why a frame is unusable, or None if it is usable."""
    if min(frame.height, frame.width) < MIN_USABLE_SIDE:
        return "too_small"
    gray = _gray(frame)
    if float(gray.std()) < BLANK_STD:
        return "blank"
    return None


def is_blurry(frame: Frame) -> bool:
    return float(cv2.Laplacian(_gray(frame), cv2.CV_64F).var()) < BLUR_VARIANCE


def _thumb(frame: Frame) -> np.ndarray:
    gray = cv2.cvtColor(frame.rgb, cv2.COLOR_RGB2GRAY)
    return cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA).astype(np.float32)


def burst_issue(burst: list[Frame]) -> str | None:
    """Return why a burst is unusable for temporal analysis, or None."""
    if any(frame_issue(f) for f in burst):
        return "bad_frames"
    thumbs = [_thumb(f) for f in burst]
    diffs = [float(np.abs(a - b).mean()) for a, b in zip(thumbs, thumbs[1:])]
    if max(diffs) > CUT_DIFF:
        return "scene_cut"
    if max(diffs) < STATIC_DIFF:
        return "static"
    return None


def assess(
    frames: list[Frame], bursts: list[list[Frame]], capture_method: str = "canvas"
) -> QualityReport:
    report = QualityReport(total_frames=len(frames) + sum(len(b) for b in bursts))
    if capture_method != "canvas":
        report.flag("screen_capture")

    blurry = 0
    for frame in frames:
        issue = frame_issue(frame)
        if issue:
            report.flag(f"frames_{issue}")
            continue
        if min(frame.height, frame.width) < LOW_RES_SIDE:
            report.flag("low_resolution")
        if is_blurry(frame):
            blurry += 1
        report.usable_frames.append(frame)
    if report.usable_frames and blurry > len(report.usable_frames) / 2:
        report.flag("blurry")

    for burst in bursts:
        issue = burst_issue(burst)
        if issue:
            report.flag(f"burst_{issue}")
        else:
            report.usable_bursts.append(burst)

    # Without sparse frames, fall back to one frame from the middle of each burst.
    if not report.usable_frames and report.usable_bursts:
        report.usable_frames = [b[len(b) // 2] for b in report.usable_bursts]
        report.flag("frames_from_bursts")

    if len(report.usable_frames) < MIN_USABLE_FRAMES:
        report.flag("few_usable_frames")
    return report
