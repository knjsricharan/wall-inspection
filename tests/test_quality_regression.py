"""
Regression tests for the AWIS-HM image quality checker.

Tests five scenarios against the quality_service.run_quality_check function
and asserts expected classifications.  Run from the project root:

    python -m pytest tests/test_quality_regression.py -v

or directly:

    python tests/test_quality_regression.py
"""

import os
import sys

# Ensure the project root is on sys.path so `backend.*` imports resolve.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import cv2
import numpy as np

from backend.schemas.quality import QualityStatus
from backend.services.quality_service import run_quality_check

# ---------------------------------------------------------------------------
# Fixture helpers — generate test images in memory
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _load_fixture(name: str) -> bytes:
    """Load a fixture image file as bytes."""
    path = os.path.join(FIXTURES_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fixture '{name}' not found at {path}. "
            "Run `python tests/generate_test_images.py` first."
        )
    with open(path, "rb") as f:
        return f.read()


def _encode_jpg(img: np.ndarray) -> bytes:
    """Encode a BGR numpy array to JPEG bytes."""
    ok, buf = cv2.imencode(".jpg", img)
    assert ok, "JPEG encoding failed"
    return buf.tobytes()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_wall_crack_image():
    """
    A wall image with a clearly visible crack.
    Expected: PASS or WARNING — must NOT be FAIL.
    """
    data = _load_fixture("wall_crack.jpg")
    result = run_quality_check(data, "wall_crack.jpg")
    print(f"\n[wall_crack.jpg]")
    print(f"  Status      : {result.status.value}")
    print(f"  Blur score  : {result.metrics.blur_score}")
    print(f"  Brightness  : {result.metrics.brightness_mean}")
    print(f"  Contrast    : {result.metrics.contrast_std}")
    print(f"  Explanation : {result.explanation}")
    assert result.status != QualityStatus.FAIL, (
        f"Wall crack image should not FAIL, got: {result.explanation}"
    )


def test_sharp_wall_image():
    """
    A clean, sharp, well-lit wall texture.
    Expected: PASS.
    """
    data = _load_fixture("sharp_wall.jpg")
    result = run_quality_check(data, "sharp_wall.jpg")
    print(f"\n[sharp_wall.jpg]")
    print(f"  Status      : {result.status.value}")
    print(f"  Blur score  : {result.metrics.blur_score}")
    print(f"  Brightness  : {result.metrics.brightness_mean}")
    print(f"  Contrast    : {result.metrics.contrast_std}")
    print(f"  Explanation : {result.explanation}")
    assert result.status == QualityStatus.PASS, (
        f"Sharp wall should PASS, got: {result.status.value} — {result.explanation}"
    )


def test_blurry_wall_image():
    """
    A heavily blurred wall (Gaussian σ=15).
    Expected: FAIL (blur score will be very low).
    """
    data = _load_fixture("blurry_wall.jpg")
    result = run_quality_check(data, "blurry_wall.jpg")
    print(f"\n[blurry_wall.jpg]")
    print(f"  Status      : {result.status.value}")
    print(f"  Blur score  : {result.metrics.blur_score}")
    print(f"  Brightness  : {result.metrics.brightness_mean}")
    print(f"  Contrast    : {result.metrics.contrast_std}")
    print(f"  Explanation : {result.explanation}")
    assert result.status == QualityStatus.FAIL, (
        f"Blurry wall should FAIL, got: {result.status.value}"
    )


def test_dark_wall_image():
    """
    A very dark / underexposed wall image.
    Expected: FAIL (mean brightness extremely low).
    """
    data = _load_fixture("dark_wall.jpg")
    result = run_quality_check(data, "dark_wall.jpg")
    print(f"\n[dark_wall.jpg]")
    print(f"  Status      : {result.status.value}")
    print(f"  Blur score  : {result.metrics.blur_score}")
    print(f"  Brightness  : {result.metrics.brightness_mean}")
    print(f"  Contrast    : {result.metrics.contrast_std}")
    print(f"  Explanation : {result.explanation}")
    assert result.status == QualityStatus.FAIL, (
        f"Dark wall should FAIL, got: {result.status.value}"
    )


def test_corrupt_file():
    """
    Random bytes — not a valid image.
    Expected: FAIL with a clear 'not a valid image' message.
    """
    data = _load_fixture("corrupt.jpg")
    result = run_quality_check(data, "corrupt.jpg")
    print(f"\n[corrupt.jpg]")
    print(f"  Status      : {result.status.value}")
    print(f"  Explanation : {result.explanation}")
    assert result.status == QualityStatus.FAIL, (
        f"Corrupt file should FAIL, got: {result.status.value}"
    )
    assert "valid image" in result.explanation.lower(), (
        "Explanation should mention invalid image"
    )


def test_original_test_image():
    """
    The original test_image.jpg from the project root (solid gray placeholder).
    This is a zero-contrast, zero-blur image — it should FAIL.
    """
    path = os.path.join(PROJECT_ROOT, "test_image.jpg")
    if not os.path.exists(path):
        print("\n[test_image.jpg] SKIPPED — file not found at project root")
        return
    with open(path, "rb") as f:
        data = f.read()
    result = run_quality_check(data, "test_image.jpg")
    print(f"\n[test_image.jpg (original placeholder)]")
    print(f"  Status      : {result.status.value}")
    print(f"  Blur score  : {result.metrics.blur_score}")
    print(f"  Brightness  : {result.metrics.brightness_mean}")
    print(f"  Contrast    : {result.metrics.contrast_std}")
    print(f"  Explanation : {result.explanation}")
    assert result.status == QualityStatus.FAIL, (
        f"Solid gray placeholder should FAIL (zero texture), "
        f"got: {result.status.value}"
    )


# ---------------------------------------------------------------------------
# Direct execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        test_wall_crack_image,
        test_sharp_wall_image,
        test_blurry_wall_image,
        test_dark_wall_image,
        test_corrupt_file,
        test_original_test_image,
    ]
    passed = 0
    failed = 0
    for fn in tests:
        name = fn.__name__
        try:
            fn()
            print(f"  >>> PASSED\n")
            passed += 1
        except AssertionError as e:
            print(f"  >>> FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  >>> ERROR: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        sys.exit(1)
