import base64
import binascii
import hashlib
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image, UnidentifiedImageError


class FrameDecodeError(ValueError):
    pass


@dataclass
class Frame:
    """A decoded RGB frame plus where it came from in the request."""

    index: int
    rgb: np.ndarray  # H x W x 3, uint8
    timestamp: float | None
    sha256: str

    @property
    def height(self) -> int:
        return self.rgb.shape[0]

    @property
    def width(self) -> int:
        return self.rgb.shape[1]


def decode_frame(data: str, index: int, timestamp: float | None, max_bytes: int) -> Frame:
    """Decode a base64 string or data URL into an RGB frame."""
    if data.startswith("data:"):
        _, _, data = data.partition(",")
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise FrameDecodeError(f"frame {index}: invalid base64") from exc
    if len(raw) > max_bytes:
        raise FrameDecodeError(f"frame {index}: larger than {max_bytes} bytes")
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise FrameDecodeError(f"frame {index}: not a decodable image") from exc
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    return Frame(index=index, rgb=rgb, timestamp=timestamp, sha256=hashlib.sha256(raw).hexdigest())
