"""Pick D3_MIDPOINT and D3_SCALE for the temporal head from labelled videos.

D3's statistic (std of second-order feature differences) has no fixed
threshold; it depends on the encoder and the kind of footage. This samples one
16-frame burst at 8 fps from the middle of each video, computes the statistic,
and chooses the midpoint that keeps the false-positive rate on real videos at
or below --max-fpr.

Usage:
    python -m scripts.calibrate_d3 --real path/to/real --fake path/to/ai [--max-fpr 0.05]

Use footage that went through the same path as production (platform
re-encode, then browser capture) or the threshold won't transfer.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

from app.config import get_settings
from app.pipeline.frames import Frame
from app.pipeline.heads.temporal import BURST_LENGTHS, REFERENCE_FPS, TemporalHead

VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".mkv", ".avi"}


def sample_burst(path: Path) -> list[Frame] | None:
    capture = cv2.VideoCapture(str(path))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    length = BURST_LENGTHS[0]
    span = int(round(length * fps / REFERENCE_FPS))
    if total < span:
        return None
    capture.set(cv2.CAP_PROP_POS_FRAMES, (total - span) // 2)
    frames: list[Frame] = []
    position = 0
    while len(frames) < length:
        ok, bgr = capture.read()
        if not ok:
            return None
        # Keep the frame nearest each 1/8 s step.
        if position >= round(len(frames) * fps / REFERENCE_FPS):
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            frames.append(Frame(len(frames), rgb, None, ""))
        position += 1
    return frames


def statistics(head: TemporalHead, folder: Path) -> list[float]:
    values = []
    for path in sorted(p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_SUFFIXES):
        burst = sample_burst(path)
        if burst is None:
            print(f"skip (too short): {path}")
            continue
        values.append(head.statistic(burst))
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--real", type=Path, required=True)
    parser.add_argument("--fake", type=Path, required=True)
    parser.add_argument("--max-fpr", type=float, default=0.05)
    args = parser.parse_args()

    head = TemporalHead(get_settings())
    real = np.array(statistics(head, args.real))
    fake = np.array(statistics(head, args.fake))
    if len(real) < 10 or len(fake) < 10:
        raise SystemExit("need at least 10 usable videos in each folder")

    # Low std means AI. Flag a video when std < midpoint; cap the share of real
    # videos below it at max_fpr.
    midpoint = float(np.quantile(real, args.max_fpr))
    scale = float(max(np.std(np.concatenate([real, fake])) / 4, 1e-6))
    tpr = float((fake < midpoint).mean())
    print(f"real: n={len(real)} median={np.median(real):.4f}")
    print(f"fake: n={len(fake)} median={np.median(fake):.4f}")
    print(f"at midpoint, real flagged={float((real < midpoint).mean()):.1%}, AI caught={tpr:.1%}")
    print(f"\nD3_MIDPOINT={midpoint:.6f}\nD3_SCALE={scale:.6f}")


if __name__ == "__main__":
    main()
