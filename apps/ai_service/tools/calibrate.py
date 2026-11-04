"""Calibrate the detection heads and the fuser on labelled videos.

Two steps, so the expensive one runs once:

    # 1. Score every video with the raw heads (GPU recommended). Resumable.
    python -m tools.calibrate run --manifest data/calib.csv --out runs/calib/scores.csv \\
        [--simulate-platform] [--sparse 16]

    # 2. Fit Platt scaling per head, a logistic-regression fuser and the verdict
    #    thresholds (CPU, seconds). Writes calibration.json and a report.
    python -m tools.calibrate fit --scores runs/calib/scores.csv --out calibration.json \\
        [--max-fpr 0.05] [--max-fnr 0.2]

    # 3. Evaluate an existing calibration on an evaluation-only set (e.g. DF26),
    #    after scoring it with `run`. Fits nothing.
    python -m tools.calibrate eval --scores runs/df26/scores.csv --calibration calibration.json

The manifest format is described in tools/manifest.py. Everything is fitted on
the "train" split and reported on the "test" split; leave split empty and a
stable 70/30 split per generator is assigned.

Point CALIBRATION_FILE at the output (default: apps/ai_service/calibration.json)
and restart the service.
"""

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.pipeline.aggregate import fuse
from app.pipeline.calibration import Calibration, Platt
from app.pipeline.detector import load_heads
from app.pipeline.heads.base import HeadResult, logit
from app.pipeline.quality import assess
from tools.manifest import assign_splits, load_manifest
from tools.sampling import sample_video, simulate_platform

HEADS = ("face", "scene", "temporal")
FIELDS = ["video_id", "path", "label", "generator", "split", "poor"] + [
    f"{h}_{k}" for h in HEADS for k in ("raw", "peak", "frames")
]


# --------------------------------------------------------------------------- run


def score_video(heads: dict, item, args, rng: random.Random) -> dict | None:
    def capture_from(path):
        return sample_video(path, sparse=args.sparse)

    if args.simulate_platform:
        with simulate_platform(item.path, rng) as platform_copy:
            capture = capture_from(platform_copy)
    else:
        capture = capture_from(item.path)
    if capture is None:
        return None

    quality = assess(capture.frames, capture.bursts)
    row = {
        "video_id": item.video_id,
        "path": str(item.path),
        "label": item.label,
        "generator": item.generator,
        "split": item.split,
        "poor": int(quality.poor),
    }
    results = {}
    if "face" in heads:
        results["face"] = heads["face"].score(quality.usable_frames)
    if "scene" in heads:
        results["scene"] = heads["scene"].score(quality.usable_frames)
    if "temporal" in heads:
        bursts = [(8.0, b) for b in quality.usable_bursts]
        results["temporal"] = heads["temporal"].score(bursts)

    for name in HEADS:
        r = results.get(name)
        raw = None
        if r is not None and r.available:
            raw = r.details.get("d3_std") if name == "temporal" else r.score
        row[f"{name}_raw"] = "" if raw is None else raw
        row[f"{name}_peak"] = "" if r is None or r.peak is None else r.peak
        row[f"{name}_frames"] = 0 if r is None else r.frames_scored
    return row


def run(args) -> None:
    items = assign_splits(load_manifest(args.manifest), holdout=args.holdout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.out.exists():
        with args.out.open() as f:
            done = {row["video_id"] for row in csv.DictReader(f)}
    todo = [i for i in items if i.video_id not in done]
    print(f"{len(items)} videos, {len(done)} already scored, {len(todo)} to go")

    heads, failed = load_heads(get_settings())
    if failed:
        sys.exit(f"heads failed to load: {failed}")
    rng = random.Random(args.seed)

    write_header = not args.out.exists()
    with args.out.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        for n, item in enumerate(todo, start=1):
            try:
                row = score_video(heads, item, args, rng)
            except Exception as exc:  # noqa: BLE001 - one bad file shouldn't stop a long run
                print(f"[{n}/{len(todo)}] error {item.path}: {exc}")
                continue
            if row is None:
                print(f"[{n}/{len(todo)}] unreadable {item.path}")
                continue
            writer.writerow(row)
            f.flush()  # so an interrupted run resumes where it stopped
            if n % 10 == 0 or n == len(todo):
                print(f"[{n}/{len(todo)}] scored")


# --------------------------------------------------------------------------- fit


def _float(value: str) -> float | None:
    return float(value) if value not in ("", None) else None


def load_scores(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for row in csv.DictReader(f):
            parsed = {
                "label": int(row["label"]),
                "generator": row["generator"],
                "split": row["split"] or "train",
                "poor": bool(int(row["poor"])),
            }
            for h in HEADS:
                parsed[f"{h}_raw"] = _float(row[f"{h}_raw"])
                parsed[f"{h}_peak"] = _float(row[f"{h}_peak"])
                parsed[f"{h}_frames"] = int(row[f"{h}_frames"] or 0)
            rows.append(parsed)
    return rows


def head_feature(name: str, raw: float) -> float:
    """What Platt scaling sees: the raw logit for probability heads, the raw
    statistic for D3."""
    return raw if name == "temporal" else logit(raw)


def fit_logistic(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float]:
    from sklearn.linear_model import LogisticRegression

    model = LogisticRegression(C=1e4, max_iter=1000)
    model.fit(x, y)
    return model.coef_[0], float(model.intercept_[0])


def head_results(row: dict, calibration: Calibration) -> list[HeadResult]:
    """Rebuild calibrated HeadResults from a scores row, as the service would."""
    results = []
    for name in HEADS:
        raw = row[f"{name}_raw"]
        if raw is None or name not in calibration.heads:
            continue
        r = HeadResult(
            name=name,
            model="",
            available=True,
            frames_scored=row[f"{name}_frames"],
            score=None if name == "temporal" else raw,
            peak=row[f"{name}_peak"],
            details={"d3_std": raw} if name == "temporal" else {},
        )
        results.append(calibration.apply(r))
    return results


class _Quality:
    def __init__(self, poor: bool):
        self.poor = poor


def verdicts(rows: list[dict], calibration: Calibration):
    settings = get_settings()
    out = []
    for row in rows:
        fused = fuse(head_results(row, calibration), _Quality(row["poor"]), settings, calibration)
        out.append((fused.verdict, fused.probability))
    return out


def auc(y: np.ndarray, p: np.ndarray) -> float | None:
    from sklearn.metrics import roc_auc_score

    if len(set(y.tolist())) < 2:
        return None
    return float(roc_auc_score(y, p))


def fit(args) -> None:
    rows = load_scores(args.scores)
    train = [r for r in rows if r["split"] in ("train", "val")]
    test = [r for r in rows if r["split"] == "test"]
    print(f"{len(rows)} scored videos: {len(train)} train, {len(test)} test")

    # 1. Platt scaling per head, on rows where the head could score.
    platts: dict[str, Platt] = {}
    for name in HEADS:
        usable = [r for r in train if r[f"{name}_raw"] is not None]
        y = np.array([r["label"] for r in usable])
        if len(usable) < args.min_per_class * 2 or min(y.sum(), len(y) - y.sum()) < args.min_per_class:
            print(f"  {name}: too few labelled rows ({len(usable)}), left uncalibrated")
            continue
        x = np.array([[head_feature(name, r[f"{name}_raw"])] for r in usable])
        coef, intercept = fit_logistic(x, y)
        platts[name] = Platt(a=float(coef[0]), b=intercept)
        print(f"  {name}: a={coef[0]:.3f} b={intercept:.3f} on {len(usable)} videos")
    if not platts:
        sys.exit("no head had enough data to calibrate")

    # 2. Fuser on calibrated logits; a head that couldn't score contributes 0.
    names = list(platts)

    def features(row):
        return [
            logit(platts[n](head_feature(n, row[f"{n}_raw"]))) if row[f"{n}_raw"] is not None else 0.0
            for n in names
        ]

    x = np.array([features(r) for r in train])
    y = np.array([r["label"] for r in train])
    weights, bias = fit_logistic(x, y)
    print("  fuser:", {n: round(float(w), 3) for n, w in zip(names, weights)}, f"bias={bias:.3f}")

    calibration = Calibration(
        heads=platts,
        fuser_weights={n: float(w) for n, w in zip(names, weights)},
        fuser_bias=bias,
        likely_ai_threshold=0.5,
        no_evidence_threshold=0.5,
    )

    # 3. Thresholds: at most max_fpr of real videos at or above likely_ai, at
    #    most max_fnr of fake videos at or below no_evidence.
    fused_train = np.array([calibration.fuse(head_results(r, calibration)) or 0.5 for r in train])
    real_p = fused_train[y == 0]
    fake_p = fused_train[y == 1]
    likely_ai = float(np.quantile(real_p, 1 - args.max_fpr)) + 1e-6
    no_evidence = float(np.quantile(fake_p, args.max_fnr))
    if no_evidence >= likely_ai:
        print("  warning: classes overlap heavily; inconclusive band collapsed")
        no_evidence = likely_ai - 1e-6
    calibration.likely_ai_threshold = min(likely_ai, 0.999)
    calibration.no_evidence_threshold = max(no_evidence, 0.0)

    # 4. Report on held-out videos, with the service's real verdict logic.
    eval_rows = test or train
    calibration.metrics = report(eval_rows, calibration, "test" if test else "train (no test split!)")
    calibration.metrics["videos"] = {"train": len(train), "eval": len(eval_rows)}
    calibration.metrics["targets"] = {"max_fpr": args.max_fpr, "max_fnr": args.max_fnr}

    data = calibration.to_json()
    data["created"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["source"] = str(args.scores)
    args.out.write_text(json.dumps(data, indent=2) + "\n")
    print(f"\nwrote {args.out}")
    print_report(calibration.metrics)
    if not test:
        print("\nwarning: no test split, so these numbers are optimistic")
    if any(math.isnan(v) for v in [calibration.likely_ai_threshold, calibration.no_evidence_threshold]):
        sys.exit("thresholds are NaN; check the scores file")


def report(rows: list[dict], calibration: Calibration, split_name: str) -> dict:
    """Metrics for `rows` under `calibration`, using the service's verdict logic."""
    ey = np.array([r["label"] for r in rows])
    results = verdicts(rows, calibration)
    fused = np.array([p if p is not None else 0.5 for _, p in results])
    calls = np.array([v for v, _ in results])

    metrics: dict = {
        "evaluated_on": split_name,
        "fused_auc": auc(ey, fused),
        "real_flagged_likely_ai": float((calls[ey == 0] == "likely_ai").mean()) if (ey == 0).any() else None,
        "fake_called_no_evidence": float((calls[ey == 1] == "no_evidence").mean()) if (ey == 1).any() else None,
        "inconclusive": float((calls == "inconclusive").mean()),
        "head_auc": {},
        "per_generator": {},
    }
    for name in calibration.heads:
        usable = [(r["label"], head_feature(name, r[f"{name}_raw"])) for r in rows if r[f"{name}_raw"] is not None]
        if usable:
            hy, hx = map(np.array, zip(*usable))
            # D3: a lower statistic means AI, so flip it for AUC.
            metrics["head_auc"][name] = auc(hy, -hx if name == "temporal" else hx)
    for generator in sorted({r["generator"] for r in rows}):
        idx = [i for i, r in enumerate(rows) if r["generator"] == generator]
        g_calls = calls[idx]
        metrics["per_generator"][generator] = {
            "n": len(idx),
            "label": "fake" if rows[idx[0]]["label"] else "real",
            "likely_ai": float((g_calls == "likely_ai").mean()),
            "inconclusive": float((g_calls == "inconclusive").mean()),
            "no_evidence": float((g_calls == "no_evidence").mean()),
        }
    return metrics


def print_report(metrics: dict) -> None:
    print(json.dumps({k: v for k, v in metrics.items() if k != "per_generator"}, indent=2))
    print("\nper generator (share of videos per verdict):")
    for g, m in metrics["per_generator"].items():
        print(
            f"  {g:<28} {m['label']:<4} n={m['n']:<5} likely_ai={m['likely_ai']:.0%} "
            f"inconclusive={m['inconclusive']:.0%} no_evidence={m['no_evidence']:.0%}"
        )


def evaluate(args) -> None:
    """Report on a scores file with an existing calibration, fitting nothing.
    Use for evaluation-only sets such as DF26."""
    rows = load_scores(args.scores)
    calibration = Calibration.load(args.calibration)
    metrics = report(rows, calibration, str(args.scores))
    metrics["videos"] = {"eval": len(rows)}
    print_report(metrics)
    if args.out:
        args.out.write_text(json.dumps(metrics, indent=2) + "\n")
        print(f"\nwrote {args.out}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate detection heads")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run", help="score labelled videos with the raw heads")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--sparse", type=int, default=16)
    p.add_argument("--holdout", type=float, default=0.3)
    p.add_argument("--simulate-platform", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.set_defaults(func=run)

    p = sub.add_parser("fit", help="fit calibration.json from a scores file")
    p.add_argument("--scores", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("calibration.json"))
    p.add_argument("--max-fpr", type=float, default=0.05, help="real videos called likely_ai")
    p.add_argument("--max-fnr", type=float, default=0.2, help="fake videos called no_evidence")
    p.add_argument("--min-per-class", type=int, default=20)
    p.set_defaults(func=fit)

    p = sub.add_parser("eval", help="report on a scores file with an existing calibration")
    p.add_argument("--scores", type=Path, required=True)
    p.add_argument("--calibration", type=Path, required=True)
    p.add_argument("--out", type=Path, help="also write the metrics as JSON")
    p.set_defaults(func=evaluate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
