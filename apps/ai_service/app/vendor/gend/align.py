# Adapted from https://github.com/yermandy/GenD (detector.py, align_face), MIT License.
# See LICENSE in this directory. GenD's models were trained on faces aligned
# exactly like this, so keep it in sync with upstream. Changes: mask handling removed.

import cv2
import numpy as np


def align_face(img: np.ndarray, landmarks: np.ndarray, scale: float = 1.3) -> np.ndarray:
    """Align a face from 5 landmarks (eyes, nose, mouth corners; image-left first).

    The output size follows the face's own size (GenD's `--target_size none`),
    so faces are never upscaled here.
    """
    dst = np.array(
        [
            [0.34, 0.46],
            [0.66, 0.46],
            [0.5, 0.64],
            [0.37, 0.82],
            [0.63, 0.82],
        ],
        dtype=np.float32,
    )

    desired_dists = np.linalg.norm(landmarks[:, None, :] - landmarks[None, :, :], axis=-1)
    dst_dists = np.linalg.norm(dst[:, None, :] - dst[None, :, :], axis=-1)
    upper = np.triu_indices(len(dst), k=1)
    approx_size = int(np.round(np.mean(desired_dists[upper] / dst_dists[upper]) * scale))
    target_size = (approx_size, approx_size)

    dst[:, 0] = dst[:, 0] * target_size[0]
    dst[:, 1] = dst[:, 1] * target_size[1]

    margin_rate = scale - 1
    x_margin = target_size[0] * margin_rate / 2.0
    y_margin = target_size[1] * margin_rate / 2.0

    dst[:, 0] += x_margin
    dst[:, 1] += y_margin

    dst[:, 0] *= target_size[0] / (target_size[0] + 2 * x_margin)
    dst[:, 1] *= target_size[1] / (target_size[1] + 2 * y_margin)

    M = cv2.estimateAffinePartial2D(landmarks.astype(np.float32), dst, method=cv2.LMEDS)[0]
    return cv2.warpAffine(img, M, target_size, flags=cv2.INTER_LINEAR)
