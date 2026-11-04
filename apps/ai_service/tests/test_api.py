import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.pipeline.detector import Detector
from app.pipeline.heads.base import FrameScore, HeadResult
from tests.conftest import pan, textured, to_data_url


class StubFrameHead:
    def __init__(self, name: str, score: float):
        self.name, self.value, self.seen = name, score, 0

    def score(self, frames):
        self.seen = len(frames)
        per_frame = [FrameScore(f.index, f.timestamp, self.value) for f in frames]
        return HeadResult(
            name=self.name, model="stub", available=True, score=self.value,
            peak=self.value, frames_scored=len(frames), per_frame=per_frame,
        )


class StubBurstHead:
    name = "temporal"

    def __init__(self):
        self.seen = 0

    def score(self, bursts):
        self.seen = len(bursts)
        return HeadResult(name="temporal", model="stub", available=True, reason="uncalibrated")


@pytest.fixture
def client():
    heads = {
        "face": StubFrameHead("face", 0.1),
        "scene": StubFrameHead("scene", 0.2),
        "temporal": StubBurstHead(),
    }
    app.state.detector = Detector(Settings(), heads, {})
    with TestClient(app) as c:
        yield c, heads
    app.state.detector = None


def body(frames: int = 6, bursts: int = 1) -> dict:
    return {
        "video": {"width": 640, "height": 480, "capture_method": "canvas"},
        "frames": [{"data": to_data_url(textured(seed=i)), "timestamp": i} for i in range(frames)],
        "bursts": [
            {"fps": 8, "frames": [{"data": to_data_url(f)} for f in pan(textured(seed=99))]}
            for _ in range(bursts)
        ],
    }


def test_health(client):
    c, _ = client
    data = c.get("/health").json()
    assert data["status"] == "ok"
    assert data["heads_loaded"] == ["face", "scene", "temporal"]


def test_analyze_video_end_to_end(client):
    c, heads = client
    response = c.post("/analyze/video", json=body())
    assert response.status_code == 200
    data = response.json()

    assert data["verdict"] == "no_evidence"
    assert data["calibrated"] is False
    assert [h["name"] for h in data["heads"]] == ["face", "scene", "temporal"]
    assert data["quality"] == {
        "total_frames": 22, "usable_frames": 6, "usable_bursts": 1, "poor": False, "flags": [],
    }
    assert len(data["frame_hashes"]) == 6
    assert heads["face"].seen == 6
    assert heads["temporal"].seen == 1


def test_rejects_empty_request(client):
    c, _ = client
    assert c.post("/analyze/video", json={"frames": [], "bursts": []}).status_code == 422


def test_rejects_undecodable_frame(client):
    c, _ = client
    response = c.post("/analyze/video", json={"frames": [{"data": "bm90IGFuIGltYWdl"}]})
    assert response.status_code == 422
    assert "not a decodable image" in response.json()["detail"]
