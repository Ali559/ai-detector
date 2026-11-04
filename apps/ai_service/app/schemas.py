from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class FrameIn(BaseModel):
    data: str = Field(..., description="Base64 image, or a data: URL (PNG or JPEG)")
    timestamp: float | None = Field(None, description="Position in the video, seconds")


class BurstIn(BaseModel):
    fps: float = Field(..., gt=0, description="Rate the burst was captured at")
    frames: list[FrameIn] = Field(..., min_length=2, max_length=32)


class VideoMeta(BaseModel):
    page_url: str | None = None
    width: int | None = Field(None, description="videoWidth of the rendition captured")
    height: int | None = Field(None, description="videoHeight of the rendition captured")
    duration: float | None = None
    capture_method: Literal["canvas", "tab_capture"] = "canvas"


class AnalyzeVideoRequest(BaseModel):
    video: VideoMeta = Field(default_factory=VideoMeta)
    frames: list[FrameIn] = Field(
        default_factory=list, max_length=64, description="Sparse frames across the video"
    )
    bursts: list[BurstIn] = Field(
        default_factory=list, max_length=4, description="Runs of consecutive frames"
    )

    @model_validator(mode="after")
    def has_frames(self) -> "AnalyzeVideoRequest":
        if not self.frames and not self.bursts:
            raise ValueError("send at least one frame or burst")
        return self


class FrameScoreOut(BaseModel):
    index: int
    timestamp: float | None
    score: float
    faces: int | None = None


class HeadOut(BaseModel):
    name: str
    model: str
    available: bool
    score: float | None = Field(None, description="P(AI) in [0, 1]; null if not scorable")
    peak: float | None = Field(None, description="Mean of the top 25% of frame scores")
    frames_scored: int
    calibrated: bool
    reason: str | None = None
    per_frame: list[FrameScoreOut] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class QualityOut(BaseModel):
    total_frames: int
    usable_frames: int
    usable_bursts: int
    poor: bool
    flags: list[str]


class AnalyzeVideoResponse(BaseModel):
    verdict: Literal["likely_ai", "inconclusive", "no_evidence"]
    probability: float | None = Field(None, description="Fused P(AI); null if nothing scored")
    calibrated: bool = Field(..., description="False until heads and fuser are calibrated")
    reasons: list[str]
    heads: list[HeadOut]
    quality: QualityOut
    frame_hashes: list[str] = Field(..., description="SHA-256 of each sparse frame, in order")
    processing_time_ms: int


class HealthResponse(BaseModel):
    status: str
    heads_loaded: list[str]
    heads_failed: dict[str, str]
    device: str
