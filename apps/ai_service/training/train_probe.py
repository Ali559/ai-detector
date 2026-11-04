"""Train the scene head's linear probe on extracted CLIP features (CPU, minutes).

    python -m training.train_probe --features runs/features --out runs/probe \\
        [--holdout-generators wan2.2,veo3.1-fast] [--val 0.2]

- Splits by video, never by frame, so near-identical frames can't leak between
  train and validation. A manifest "split" of "test" is respected; otherwise a
  stable 20% of videos per generator is held out.
- --holdout-generators keeps those generators out of training entirely. That's
  the honest measure of how the probe handles a generator it has never seen.
- Fits L2-regularised logistic regression on per-crop features (balanced
  classes), picking the regularisation by validation AUC.
- Scores videos the way the service does: mean of crop logits per frame, mean
  of frame logits per video.

Writes scene_probe.pth (load it with SCENE_HEAD_WEIGHTS) and metrics.json.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def load_features(folder: Path) -> list[dict]:
    videos = []
    for path in sorted(folder.glob("*.npz")):
        if path.name.endswith(".tmp.npz"):
            continue
        with np.load(path) as data:
            videos.append(
                {
                    "features": data["features"].astype(np.float32),  # (frames, 5, 768)
                    "label": int(data["label"]),
                    "generator": str(data["generator"]),
                    "split": str(data["split"]),
                    "video_id": str(data["video_id"]),
                }
            )
    return videos


def is_validation(video: dict, holdout_generators: set[str], fraction: float) -> bool:
    if video["generator"] in holdout_generators or video["split"] == "test":
        return True
    if video["split"] == "train":
        return False
    digest = hashlib.sha1(f"{video['generator']}:{video['video_id']}".encode()).digest()
    return digest[0] / 255 < fraction


def video_scores(model, videos: list[dict]) -> np.ndarray:
    """Mean crop logit per frame, then mean frame logit per video."""
    return np.array(
        [model.decision_function(v["features"].reshape(-1, v["features"].shape[-1])).mean() for v in videos]
    )


def tpr_at_fpr(y: np.ndarray, s: np.ndarray, fpr: float) -> float | None:
    if not (y == 0).any() or not (y == 1).any():
        return None
    threshold = np.quantile(s[y == 0], 1 - fpr)
    return float((s[y == 1] > threshold).mean())


def main() -> None:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--features", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--holdout-generators", default="")
    parser.add_argument("--val", type=float, default=0.2)
    args = parser.parse_args()

    videos = load_features(args.features)
    holdout = {g.strip() for g in args.holdout_generators.split(",") if g.strip()}
    train = [v for v in videos if not is_validation(v, holdout, args.val)]
    val = [v for v in videos if is_validation(v, holdout, args.val)]
    if not train or not val:
        raise SystemExit("need videos in both train and validation")
    for name, part in (("train", train), ("val", val)):
        labels = [v["label"] for v in part]
        print(f"{name}: {len(part)} videos ({sum(labels)} fake, {len(labels) - sum(labels)} real)")

    def stack(part):
        x = np.concatenate([v["features"].reshape(-1, v["features"].shape[-1]) for v in part])
        y = np.concatenate([np.full(v["features"].shape[0] * v["features"].shape[1], v["label"]) for v in part])
        return x, y

    x_train, y_train = stack(train)
    y_val = np.array([v["label"] for v in val])

    best = None
    for c in (0.01, 0.1, 1.0, 10.0):
        model = LogisticRegression(C=c, class_weight="balanced", max_iter=2000)
        model.fit(x_train, y_train)
        val_auc = roc_auc_score(y_val, video_scores(model, val)) if len(set(y_val)) > 1 else float("nan")
        print(f"  C={c:<5} val AUC={val_auc:.4f}")
        if best is None or val_auc > best[0]:
            best = (val_auc, c, model)
    val_auc, c, model = best

    scores = video_scores(model, val)
    metrics = {
        "C": c,
        "videos": {"train": len(train), "val": len(val)},
        "holdout_generators": sorted(holdout),
        "val_auc": val_auc,
        "val_tpr_at_5pct_fpr": tpr_at_fpr(y_val, scores, 0.05),
        "per_generator": {},
    }
    real_scores = scores[y_val == 0]
    threshold = float(np.quantile(real_scores, 0.95)) if len(real_scores) else 0.0
    for generator in sorted({v["generator"] for v in val}):
        idx = [i for i, v in enumerate(val) if v["generator"] == generator]
        label = val[idx[0]]["label"]
        flagged = float((scores[idx] > threshold).mean())
        metrics["per_generator"][generator] = {
            "n": len(idx),
            "label": "fake" if label else "real",
            # For fakes: caught at the 5%-FPR threshold. For reals: false alarms.
            "flagged_at_5pct_fpr": flagged,
            "held_out": generator in holdout,
        }

    args.out.mkdir(parents=True, exist_ok=True)
    state = {
        "weight": torch.tensor(model.coef_, dtype=torch.float32),
        "bias": torch.tensor(model.intercept_, dtype=torch.float32),
    }
    torch.save(state, args.out / "scene_probe.pth")
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metrics.items() if k != "per_generator"}, indent=2))
    for g, m in metrics["per_generator"].items():
        tag = " (held out)" if m["held_out"] else ""
        print(f"  {g:<28} {m['label']:<4} n={m['n']:<5} flagged={m['flagged_at_5pct_fpr']:.0%}{tag}")
    print(f"\nwrote {args.out / 'scene_probe.pth'}; set SCENE_HEAD_WEIGHTS to use it")


if __name__ == "__main__":
    main()
