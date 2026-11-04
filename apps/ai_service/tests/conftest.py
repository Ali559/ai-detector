import base64
import io

import numpy as np
import pytest
from PIL import Image

from app.pipeline.frames import Frame


def textured(height: int = 480, width: int = 640, seed: int = 0) -> np.ndarray:
    """A smooth gradient plus noise: has detail, isn't blank, isn't blurry."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width]
    base = np.stack([x * 255 / width, y * 255 / height, (x + y) * 127 / (width + height)], -1)
    return np.clip(base + rng.normal(0, 25, (height, width, 3)), 0, 255).astype(np.uint8)


def make_frame(rgb: np.ndarray, index: int = 0) -> Frame:
    return Frame(index=index, rgb=rgb, timestamp=float(index), sha256=f"hash{index}")


def to_data_url(rgb: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(rgb).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def pan(rgb: np.ndarray, n: int = 16, step: int = 3) -> list[np.ndarray]:
    return [np.roll(rgb, i * step, axis=1) for i in range(n)]


@pytest.fixture
def frame_factory():
    return make_frame
