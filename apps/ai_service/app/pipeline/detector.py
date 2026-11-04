import logging
import threading
import time
from dataclasses import asdict

from app.config import Settings
from app.pipeline.aggregate import fuse
from app.pipeline.calibration import Calibration
from app.pipeline.frames import Frame, decode_frame
from app.pipeline.heads.base import HeadResult
from app.pipeline.quality import assess
from app.schemas import AnalyzeVideoRequest, AnalyzeVideoResponse, HeadOut, QualityOut

log = logging.getLogger(__name__)

HEAD_MODELS = {
    "face": "app.pipeline.heads.face:FaceHead",
    "scene": "app.pipeline.heads.scene:SceneHead",
    "temporal": "app.pipeline.heads.temporal:TemporalHead",
}


def load_heads(settings: Settings) -> tuple[dict[str, object], dict[str, str]]:
    """Load each enabled head. A head that fails to load is reported, not fatal."""
    import importlib

    heads: dict[str, object] = {}
    failed: dict[str, str] = {}
    for name in settings.enabled_heads:
        target = HEAD_MODELS.get(name)
        if target is None:
            failed[name] = "unknown head"
            continue
        module, cls = target.split(":")
        try:
            heads[name] = getattr(importlib.import_module(module), cls)(settings)
            log.info("loaded %s head", name)
        except Exception as exc:  # noqa: BLE001 - surface any load failure in /health
            log.exception("failed to load %s head", name)
            failed[name] = str(exc)
    return heads, failed


class Detector:
    def __init__(self, settings: Settings, heads: dict[str, object], failed: dict[str, str]):
        self.settings = settings
        self.heads = heads
        self.failed = failed
        self.calibration = (
            Calibration.load(settings.calibration_file)
            if settings.calibration_file.is_file()
            else None
        )
        if self.calibration:
            log.info("using calibration from %s", settings.calibration_file)
        # Heads share one device; run one request at a time.
        self._lock = threading.Lock()

    def analyze(self, request: AnalyzeVideoRequest) -> AnalyzeVideoResponse:
        started = time.perf_counter()
        max_bytes = self.settings.max_frame_bytes

        frames = [decode_frame(f.data, i, f.timestamp, max_bytes) for i, f in enumerate(request.frames)]
        bursts: list[tuple[float, list[Frame]]] = []
        index = len(frames)
        for burst in request.bursts:
            decoded = []
            for f in burst.frames:
                decoded.append(decode_frame(f.data, index, f.timestamp, max_bytes))
                index += 1
            bursts.append((burst.fps, decoded))

        quality = assess(frames, [b for _, b in bursts], request.video.capture_method)
        usable_bursts = [(fps, b) for fps, b in bursts if any(b is u for u in quality.usable_bursts)]

        results: list[HeadResult] = []
        with self._lock:
            for name in ("face", "scene"):
                head = self.heads.get(name)
                if head is not None:
                    results.append(head.score(quality.usable_frames))
            temporal = self.heads.get("temporal")
            if temporal is not None:
                results.append(temporal.score(usable_bursts))
        for name, error in self.failed.items():
            results.append(HeadResult.unavailable(name, "", f"failed_to_load: {error}"))

        if self.calibration:
            results = [self.calibration.apply(r) for r in results]
        fused = fuse(results, quality, self.settings, self.calibration)
        scored = [r for r in results if r.score is not None]
        return AnalyzeVideoResponse(
            verdict=fused.verdict,
            probability=fused.probability,
            calibrated=bool(scored) and all(r.calibrated for r in scored),
            reasons=fused.reasons,
            heads=[HeadOut(**asdict(r)) for r in results],
            quality=QualityOut(
                total_frames=quality.total_frames,
                usable_frames=len(quality.usable_frames),
                usable_bursts=len(quality.usable_bursts),
                poor=quality.poor,
                flags=quality.flags,
            ),
            frame_hashes=[f.sha256 for f in frames],
            processing_time_ms=int((time.perf_counter() - started) * 1000),
        )
