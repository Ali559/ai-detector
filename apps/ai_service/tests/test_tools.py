import shutil
import subprocess

import numpy as np
import pytest

from app.pipeline.heads.scene import native_crops
from tools.manifest import assign_splits, load_manifest
from tools.sampling import BURST_LENGTH, sample_video

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def test_manifest_parses_and_splits_stably(tmp_path):
    manifest = tmp_path / "m.csv"
    manifest.write_text(
        "path,label,generator,split\n"
        "a.mp4,real,cam,\n"
        "b.mp4,fake,wan,test\n"
        + "".join(f"v{i}.mp4,fake,wan,\n" for i in range(50))
    )
    items = load_manifest(manifest)
    assert items[0].path == tmp_path / "a.mp4" and items[0].label == 0
    assert items[1].label == 1 and items[1].split == "test"

    first = assign_splits(items)
    assert [i.split for i in assign_splits(items)] == [i.split for i in first]
    assert first[1].split == "test"
    assert 5 < sum(i.split == "test" for i in first) < 30


def test_manifest_rejects_bad_label(tmp_path):
    manifest = tmp_path / "m.csv"
    manifest.write_text("path,label,generator,split\na.mp4,maybe,x,\n")
    with pytest.raises(ValueError, match="real or fake"):
        load_manifest(manifest)


def test_crops_avoid_borders_on_large_frames():
    rgb = np.zeros((720, 1280, 3), np.uint8)
    rgb[72:-72, 128:-128] = 255  # everything outside the 10% border is white
    assert all(c.min() == 255 for c in native_crops(rgb))


def test_crops_still_fit_small_frames():
    assert all(c.shape == (224, 224, 3) for c in native_crops(np.zeros((240, 320, 3), np.uint8)))


@needs_ffmpeg
def test_sample_video_matches_extension_capture(tmp_path):
    video = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30",
         "-t", "6", "-pix_fmt", "yuv420p", str(video)],
        check=True,
    )
    capture = sample_video(video, sparse=8, burst_starts=(0.3, 0.9))
    assert len(capture.frames) == 8
    assert (capture.width, capture.height) == (640, 360)
    # 2 s bursts: the one at 30% fits, the one at 90% would run past the end.
    assert len(capture.bursts) == 1 and len(capture.bursts[0]) == BURST_LENGTH
    times = [f.timestamp for f in capture.bursts[0]]
    assert np.allclose(np.diff(times), 1 / 8)
    assert capture.frames[0].timestamp == pytest.approx(6 * (0.02 + 0.96 * 0.5 / 8))
