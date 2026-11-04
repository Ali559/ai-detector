"""Extract frozen CLIP features for training the scene probe.

The only GPU-heavy training step. For each video in the manifest it samples
frames exactly as the extension would (tools/sampling.py), optionally
re-encodes the video like a platform first, and stores the CLIP ViT-L/14
embedding of each of the scene head's 5 crops per frame.

Output is one small .npz per video in --out, so the job is resumable: rerun
the same command after an interruption (spot/interruptible GPUs are fine) and
finished videos are skipped. 1,000 videos x 8 frames x 5 crops in fp16 is about
60 MB, so the videos themselves can be deleted afterwards.

    python -m training.extract_features --manifest data/train.csv --out runs/features \\
        [--frames 8] [--simulate-platform] [--platform-copies 1]
"""

import argparse
import random
import sys
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.pipeline.heads.scene import SceneHead
from app.pipeline.quality import frame_issue
from tools.manifest import load_manifest
from tools.sampling import sample_video, simulate_platform


def extract(head: SceneHead, path: Path, frames: int) -> np.ndarray | None:
    capture = sample_video(path, sparse=frames, burst_starts=())
    if capture is None:
        return None
    rows = []
    for frame in capture.frames:
        if frame_issue(frame):
            continue
        features = head.features(frame)
        if features is not None:
            rows.append(features.float().cpu().numpy())
    return np.stack(rows).astype(np.float16) if rows else None  # (frames, 5, 768)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--frames", type=int, default=8, help="sparse frames per video")
    parser.add_argument(
        "--simulate-platform",
        action="store_true",
        help="re-encode each video like a video platform before sampling (needs ffmpeg)",
    )
    parser.add_argument(
        "--platform-copies",
        type=int,
        default=1,
        help="with --simulate-platform: independent re-encodes per video (augmentation)",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    items = load_manifest(args.manifest)
    args.out.mkdir(parents=True, exist_ok=True)
    head = SceneHead(get_settings())
    print(f"backbone {head.model_name} on {head.device}; {len(items)} videos")

    copies = args.platform_copies if args.simulate_platform else 1
    for n, item in enumerate(items, start=1):
        for copy in range(copies):
            target = args.out / f"{item.video_id}_{copy}.npz"
            if target.exists():
                continue
            try:
                if args.simulate_platform:
                    rng = random.Random(f"{args.seed}:{item.video_id}:{copy}")
                    with simulate_platform(item.path, rng) as platform_copy:
                        features = extract(head, platform_copy, args.frames)
                else:
                    features = extract(head, item.path, args.frames)
            except Exception as exc:  # noqa: BLE001 - skip bad files, keep going
                print(f"[{n}/{len(items)}] error {item.path}: {exc}", file=sys.stderr)
                continue
            if features is None:
                print(f"[{n}/{len(items)}] no usable frames: {item.path}", file=sys.stderr)
                continue
            # Write to a temp name first so a killed job never leaves a half file.
            tmp = target.with_suffix(".tmp.npz")
            np.savez(
                tmp,
                features=features,
                label=item.label,
                generator=item.generator,
                split=item.split,
                video_id=item.video_id,
            )
            tmp.rename(target)
        if n % 25 == 0 or n == len(items):
            print(f"[{n}/{len(items)}] done")


if __name__ == "__main__":
    main()
