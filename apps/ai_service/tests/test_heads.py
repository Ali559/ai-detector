"""Tests for the model-independent parts of each head."""

import numpy as np
import torch

from app.pipeline.heads.face import yunet_landmarks
from app.pipeline.heads.scene import native_crops
from app.pipeline.heads.temporal import second_order_std, trim_burst
from app.vendor.gend.align import align_face
from tests.conftest import make_frame, textured


def test_second_order_std_matches_d3_definition():
    # Feature distances 1, 2, 4, 7 → second-order diffs 1, 2, 3 → std 1.
    steps = [0.0, 1.0, 3.0, 7.0, 14.0]
    features = torch.tensor([[s, 0.0] for s in steps])
    assert second_order_std(features) == 1.0


def test_constant_motion_has_zero_second_order_std():
    features = torch.tensor([[float(i), 0.0] for i in range(16)])
    assert second_order_std(features) == 0.0


def test_trim_burst_prefers_16_then_8():
    burst = [make_frame(textured(32, 32), i) for i in range(20)]
    assert [f.index for f in trim_burst(burst)] == list(range(2, 18))
    assert len(trim_burst(burst[:10])) == 8
    assert trim_burst(burst[:5]) is None


def test_native_crops_never_resize():
    crops = native_crops(textured(720, 1280))
    assert len(crops) == 5
    assert all(c.shape == (224, 224, 3) for c in crops)


def test_yunet_landmarks_are_ordered_image_left_first():
    # x, y, w, h, then (right eye, left eye, nose, right mouth, left mouth), score.
    row = np.array([0, 0, 100, 100, 70, 40, 30, 40, 50, 60, 65, 80, 35, 80, 0.9])
    pts = yunet_landmarks(row)
    assert pts[0][0] < pts[1][0]
    assert pts[3][0] < pts[4][0]
    assert tuple(pts[2]) == (50, 60)


def test_align_face_keeps_native_scale():
    landmarks = np.array([[270, 280], [370, 280], [320, 330], [280, 380], [360, 380]], np.float32)
    crop = align_face(textured(), landmarks)
    assert crop.shape[0] == crop.shape[1]
    # GenD sizes the crop from the face itself: ~1.3x the landmark spread.
    assert 300 < crop.shape[0] < 450
