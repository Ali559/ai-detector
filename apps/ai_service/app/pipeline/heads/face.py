"""Face head: YuNet face detection → GenD-aligned crops → GenD classifier.

Catches face swaps, reenactment and lip-sync. Frames without a usable face are
skipped, and a video with no faces leaves this head unavailable rather than
counting as "real".
"""

import cv2
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from PIL import Image

from app.config import Settings
from app.pipeline.frames import Frame
from app.pipeline.heads.base import FrameScore, HeadResult, resolve_device, summarise
from app.vendor.gend.align import align_face

YUNET_REPO = "opencv/face_detection_yunet"
YUNET_FILE = "face_detection_yunet_2023mar.onnx"


def yunet_landmarks(row: np.ndarray) -> np.ndarray:
    """YuNet row → 5x2 landmarks in GenD's order (image-left eye first)."""
    pts = row[4:14].reshape(5, 2).astype(np.float32)
    eyes = pts[[0, 1]][np.argsort(pts[[0, 1], 0])]
    mouth = pts[[3, 4]][np.argsort(pts[[3, 4], 0])]
    return np.stack([eyes[0], eyes[1], pts[2], mouth[0], mouth[1]])


class FaceHead:
    name = "face"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = resolve_device(settings.device)
        if self.device.type == "mps":
            # GenD-PE's timm backbone aborts the process on MPS (torch 2.8,
            # "MPSNDArray ... buffer is not large enough"), so run it on CPU.
            self.device = torch.device("cpu")
        self.model_name = settings.gend_model

        yunet_path = hf_hub_download(YUNET_REPO, YUNET_FILE, cache_dir=settings.weights_dir)
        self.detector = cv2.FaceDetectorYN.create(
            yunet_path, "", (320, 320), score_threshold=settings.face_score_threshold
        )

        from app.vendor.gend.modeling_gend import GenD

        self.model = GenD.from_pretrained(self.model_name, cache_dir=settings.weights_dir)
        self.model.to(self.device).eval()

    def detect(self, frame: Frame) -> list[np.ndarray]:
        bgr = cv2.cvtColor(frame.rgb, cv2.COLOR_RGB2BGR)
        self.detector.setInputSize((frame.width, frame.height))
        _, faces = self.detector.detect(bgr)
        if faces is None:
            return []
        faces = [f for f in faces if min(f[2], f[3]) >= self.settings.face_min_size]
        faces.sort(key=lambda f: f[2] * f[3], reverse=True)
        return faces[: self.settings.max_faces_per_frame]

    @torch.no_grad()
    def score(self, frames: list[Frame]) -> HeadResult:
        per_frame: list[FrameScore] = []
        for frame in frames:
            faces = self.detect(frame)
            if not faces:
                continue
            crops = [Image.fromarray(align_face(frame.rgb, yunet_landmarks(f))) for f in faces]
            batch = torch.stack([self.model.feature_extractor.preprocess(c) for c in crops])
            probs = self.model(batch.to(self.device)).softmax(dim=-1)[:, 1]
            # A frame is as suspicious as its most suspicious face.
            per_frame.append(
                FrameScore(frame.index, frame.timestamp, float(probs.max()), faces=len(faces))
            )

        if not per_frame:
            return HeadResult.unavailable(self.name, self.model_name, "no_faces")
        score, peak = summarise(per_frame)
        return HeadResult(
            name=self.name,
            model=self.model_name,
            available=True,
            score=score,
            peak=peak,
            frames_scored=len(per_frame),
            calibrated=False,
            per_frame=per_frame,
        )
