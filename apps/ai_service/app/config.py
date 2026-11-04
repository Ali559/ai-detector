import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SERVICE_ROOT = Path(__file__).resolve().parent.parent


def _float(name: str, default: float | None) -> float | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _heads() -> tuple[str, ...]:
    raw = os.getenv("ENABLED_HEADS", "face,scene,temporal")
    return tuple(h.strip() for h in raw.split(",") if h.strip())


@dataclass(frozen=True)
class Settings:
    """Runtime configuration, read from the environment (see .env.example)."""

    enabled_heads: tuple[str, ...] = field(default_factory=_heads)
    device: str = field(default_factory=lambda: os.getenv("DEVICE", "auto"))
    weights_dir: Path = field(
        default_factory=lambda: Path(os.getenv("WEIGHTS_DIR", SERVICE_ROOT / "weights"))
    )

    # Face head: YuNet face detector + GenD classifier
    gend_model: str = field(default_factory=lambda: os.getenv("GEND_MODEL", "yermandy/GenD_PE_L"))
    face_min_size: int = 64
    face_score_threshold: float = 0.7
    max_faces_per_frame: int = 3

    # Scene head: UnivFD linear probe on frozen CLIP ViT-L/14
    scene_backbone: str = field(
        default_factory=lambda: os.getenv("SCENE_BACKBONE", "openai/clip-vit-large-patch14")
    )
    scene_head_weights: Path = field(
        default_factory=lambda: Path(
            os.getenv("SCENE_HEAD_WEIGHTS", SERVICE_ROOT / "weights" / "univfd_fc.pth")
        )
    )

    # Temporal head: D3 (training-free). Its raw statistic only becomes a
    # probability through calibration.json.
    temporal_encoder: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_ENCODER", "microsoft/xclip-base-patch16")
    )

    # Fitted by tools/calibrate.py. When present it supersedes the bands below.
    calibration_file: Path = field(
        default_factory=lambda: Path(
            os.getenv("CALIBRATION_FILE", SERVICE_ROOT / "calibration.json")
        )
    )

    # Verdict bands used without calibration. Deliberately conservative:
    # calling a real video fake is the costlier mistake.
    likely_ai_threshold: float = field(
        default_factory=lambda: _float("LIKELY_AI_THRESHOLD", 0.85) or 0.85
    )
    no_evidence_threshold: float = field(
        default_factory=lambda: _float("NO_EVIDENCE_THRESHOLD", 0.35) or 0.35
    )
    strong_head_threshold: float = 0.95
    strong_head_min_frames: int = 3

    # Request limits
    max_frame_bytes: int = 8 * 1024 * 1024

    # When set, /analyze/video requires "Authorization: Bearer <SERVICE_TOKEN>".
    # Set it whenever the service is reachable from the internet.
    service_token: str | None = field(default_factory=lambda: os.getenv("SERVICE_TOKEN") or None)


def get_settings() -> Settings:
    return Settings()
