import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.pipeline.detector import Detector, load_heads
from app.pipeline.frames import FrameDecodeError
from app.pipeline.heads.base import resolve_device
from app.schemas import AnalyzeVideoRequest, AnalyzeVideoResponse, HealthResponse

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tests set app.state.detector themselves to avoid loading models.
    if getattr(app.state, "detector", None) is None:
        settings = get_settings()
        heads, failed = load_heads(settings)
        app.state.detector = Detector(settings, heads, failed)
    yield


app = FastAPI(
    title="AI Video Detection Service",
    description="Internal service: scores video frames for signs of AI generation",
    version="2.0.0",
    lifespan=lifespan,
)

# The service is meant to sit behind apps/api. CORS is open so the extension
# can call it directly during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    detector: Detector = app.state.detector
    return HealthResponse(
        status="ok" if detector.heads else "degraded",
        heads_loaded=list(detector.heads),
        heads_failed=detector.failed,
        device=str(resolve_device(detector.settings.device)),
    )


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = app.state.detector.settings.service_token
    if expected is None:
        return
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid service token")


@app.post("/analyze/video", response_model=AnalyzeVideoResponse, dependencies=[Depends(require_token)])
def analyze_video(request: AnalyzeVideoRequest) -> AnalyzeVideoResponse:
    detector: Detector = app.state.detector
    if not detector.heads:
        raise HTTPException(status_code=503, detail="No detection heads loaded")
    try:
        return detector.analyze(request)
    except FrameDecodeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
