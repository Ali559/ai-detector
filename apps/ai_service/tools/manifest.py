"""Video manifests: the one input format for calibration and training.

A manifest is a CSV with a header row:

    path,label,generator,split
    data/real/clip001.mp4,real,real-youtube,
    data/fake/wan_0001.mp4,fake,wan2.2-ti2v-5b,test

- path:      video file, relative to the manifest's folder or absolute
- label:     "real" or "fake"
- generator: where the video came from (a generator name, or the real source).
             Used for per-generator metrics and generator-held-out splits.
- split:     optional "train" / "val" / "test"; empty means "decide for me"
"""

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Item:
    path: Path
    label: int  # 1 = fake (AI-generated), 0 = real
    generator: str
    split: str

    @property
    def video_id(self) -> str:
        return hashlib.sha1(str(self.path).encode()).hexdigest()[:16]


def load_manifest(manifest: Path) -> list[Item]:
    items = []
    with manifest.open(newline="") as f:
        for row_number, row in enumerate(csv.DictReader(f), start=2):
            label = row["label"].strip().lower()
            if label not in ("real", "fake"):
                raise ValueError(f"{manifest}:{row_number}: label must be real or fake")
            path = Path(row["path"].strip())
            if not path.is_absolute():
                path = manifest.parent / path
            items.append(
                Item(
                    path=path,
                    label=int(label == "fake"),
                    generator=(row.get("generator") or label).strip(),
                    split=(row.get("split") or "").strip().lower(),
                )
            )
    return items


def assign_splits(items: list[Item], holdout: float = 0.3, seed: int = 0) -> list[Item]:
    """Fill empty splits with train/test, stratified by generator and stable per
    video (hash-based), so re-running never moves a video between splits."""
    out = []
    for item in items:
        if item.split:
            out.append(item)
            continue
        digest = hashlib.sha1(f"{seed}:{item.generator}:{item.path}".encode()).digest()
        split = "test" if digest[0] / 255 < holdout else "train"
        out.append(Item(item.path, item.label, item.generator, split))
    return out
