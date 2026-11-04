"""Turn a video file into the frames the browser extension would have sent.

Calibration and training must see frames that went through the same path as
production, or the models learn (and calibrate on) the wrong artefacts. This
mirrors apps/extension/src/content/content.ts:

- sparse frames spread across the video, skipping the first and last 2%;
- bursts of 16 frames at 8 fps;
- each frame encoded as JPEG at quality 95, then decoded again;
- frames capped at 1920 px on the long side, never upscaled.

`simulate_platform` additionally re-encodes the video the way a video platform
would (H.264 at a random CRF and resolution), applied identically to real and
fake videos so the codec can't become a label shortcut.
"""

import random
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.pipeline.frames import Frame

BURST_FPS = 8.0
BURST_LENGTH = 16
JPEG_QUALITY = 95
MAX_LONG_SIDE = 1920
PLATFORM_HEIGHTS = (480, 720, 1080)
PLATFORM_CRF = (23, 35)


@dataclass
class Capture:
    frames: list[Frame]
    bursts: list[list[Frame]]
    width: int
    height: int
    duration: float


def _browser_frame(bgr: np.ndarray, index: int, timestamp: float) -> Frame:
    h, w = bgr.shape[:2]
    scale = min(1.0, MAX_LONG_SIDE / max(h, w))
    if scale < 1:
        bgr = cv2.resize(bgr, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    ok, jpeg = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if not ok:
        raise ValueError("JPEG encode failed")
    rgb = cv2.cvtColor(cv2.imdecode(jpeg, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return Frame(index=index, rgb=rgb, timestamp=timestamp, sha256="")


def _read_at(capture: cv2.VideoCapture, frame_number: int) -> np.ndarray | None:
    capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ok, bgr = capture.read()
    return bgr if ok else None


def sample_video(
    path: Path, sparse: int = 16, burst_starts: tuple[float, ...] = (0.3, 0.6)
) -> Capture | None:
    """Sample sparse frames and bursts. Returns None if the video can't be read."""
    capture = cv2.VideoCapture(str(path))
    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if total < 2:
            return None
        duration = total / fps
        index = 0

        frames = []
        for i in range(sparse):
            t = duration * (0.02 + 0.96 * (i + 0.5) / sparse)
            bgr = _read_at(capture, min(int(t * fps), total - 1))
            if bgr is not None:
                frames.append(_browser_frame(bgr, index, t))
                index += 1

        bursts = []
        span = BURST_LENGTH / BURST_FPS
        for start in burst_starts:
            t0 = duration * start
            if t0 + span > duration:
                continue
            burst = []
            for k in range(BURST_LENGTH):
                t = t0 + k / BURST_FPS
                bgr = _read_at(capture, min(round(t * fps), total - 1))
                if bgr is None:
                    break
                burst.append(_browser_frame(bgr, index, t))
                index += 1
            if len(burst) == BURST_LENGTH:
                bursts.append(burst)

        if not frames:
            return None
        h, w = frames[0].rgb.shape[:2]
        return Capture(frames=frames, bursts=bursts, width=w, height=h, duration=duration)
    finally:
        capture.release()


@contextmanager
def simulate_platform(path: Path, rng: random.Random):
    """Yield a copy of the video re-encoded like a video platform would."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("simulate_platform needs ffmpeg on PATH")
    capture = cv2.VideoCapture(str(path))
    source_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    heights = [h for h in PLATFORM_HEIGHTS if h <= source_height] or [source_height]
    height = rng.choice(heights)
    crf = rng.randint(*PLATFORM_CRF)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "platform.mp4"
        subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-y", "-i", str(path),
                "-vf", f"scale=-2:{height}", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", str(crf), "-pix_fmt", "yuv420p", "-an", str(out),
            ],
            check=True,
        )
        yield out
