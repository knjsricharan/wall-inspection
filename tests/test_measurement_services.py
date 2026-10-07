import os
import sys

import cv2
import numpy as np
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.services.measurement_service import measure_crack_mask
from backend.services.postprocess_service import MaskPostprocessConfig, postprocess_mask


def test_empty_mask_returns_zero_measurements():
    mask = np.zeros((40, 40), dtype=np.uint8)

    measurement = measure_crack_mask(mask)

    assert measurement.area_px2 == 0
    assert measurement.length_px == 0
    assert measurement.width_px == 0
    assert measurement.max_width_px == 0
    assert measurement.measurement_unit == "pixel"
    assert measurement.calibrated is False


def test_small_isolated_noise_removed_when_threshold_allows():
    mask = np.zeros((40, 40), dtype=np.uint8)
    mask[5, 5] = 1
    cv2.line(mask, (10, 20), (25, 20), 1, 1)

    cleaned = postprocess_mask(
        mask,
        config=MaskPostprocessConfig(min_region_area_px=5, closing_kernel_size=0, closing_iterations=0),
    )

    assert cleaned[5, 5] == 0
    assert int(np.count_nonzero(cleaned)) == 16


def test_simple_straight_crack_measurements_are_reasonable():
    mask = np.zeros((50, 50), dtype=np.uint8)
    cv2.line(mask, (10, 25), (30, 25), 1, 1)

    measurement = measure_crack_mask(mask)

    assert measurement.area_px2 == 21
    assert 19 <= measurement.length_px <= 21
    assert 1.5 <= measurement.width_px <= 2.5
    assert abs(measurement.orientation_deg or 0) <= 1


def test_diagonal_crack_length_accounts_for_diagonal_geometry():
    mask = np.zeros((50, 50), dtype=np.uint8)
    for offset in range(21):
        mask[10 + offset, 10 + offset] = 1

    measurement = measure_crack_mask(mask)

    assert 27.5 <= measurement.length_px <= 29.5
    assert 40 <= (measurement.orientation_deg or 0) <= 50


def test_wider_crack_reports_larger_width():
    narrow = np.zeros((80, 80), dtype=np.uint8)
    wide = np.zeros((80, 80), dtype=np.uint8)
    cv2.line(narrow, (10, 40), (60, 40), 1, 1)
    cv2.line(wide, (10, 40), (60, 40), 1, 7)

    narrow_measurement = measure_crack_mask(narrow)
    wide_measurement = measure_crack_mask(wide)

    assert wide_measurement.width_px > narrow_measurement.width_px
    assert wide_measurement.max_width_px > narrow_measurement.max_width_px
    assert wide_measurement.area_px2 > narrow_measurement.area_px2


def test_multiple_disconnected_crack_regions_remain_when_large_enough():
    mask = np.zeros((60, 60), dtype=np.uint8)
    cv2.line(mask, (5, 15), (25, 15), 1, 1)
    cv2.line(mask, (35, 45), (55, 45), 1, 1)

    cleaned = postprocess_mask(
        mask,
        config=MaskPostprocessConfig(min_region_area_px=5, closing_kernel_size=0, closing_iterations=0),
    )
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(cleaned, connectivity=8)

    assert num_labels - 1 == 2


def test_invalid_malformed_mask_raises_graceful_value_error():
    with pytest.raises(ValueError, match="two-dimensional"):
        measure_crack_mask(np.zeros((10, 10, 3), dtype=np.uint8))

    with pytest.raises(ValueError, match="empty"):
        postprocess_mask(np.zeros((0, 0), dtype=np.uint8))
