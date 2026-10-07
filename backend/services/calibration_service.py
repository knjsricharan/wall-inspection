"""Image-specific ArUco calibration for pixel-to-millimetre conversion."""

from dataclasses import dataclass
from math import hypot

import cv2
import numpy as np


@dataclass(frozen=True)
class CalibrationResult:
    calibrated: bool
    marker_detected: bool
    marker_id: int | None
    marker_size_mm: float
    marker_pixel_size: float | None
    pixels_per_mm: float | None
    calibration_status: str
    calibration_quality: str
    corners: np.ndarray | None = None


def _failed(marker_size_mm: float, status: str, marker_detected: bool = False) -> CalibrationResult:
    return CalibrationResult(
        calibrated=False,
        marker_detected=marker_detected,
        marker_id=None,
        marker_size_mm=marker_size_mm,
        marker_pixel_size=None,
        pixels_per_mm=None,
        calibration_status=status,
        calibration_quality="invalid",
    )


def calculate_marker_scale(side_lengths: np.ndarray, marker_size_mm: float, min_marker_side_px: float = 20.0, max_side_variation_ratio: float = 0.25) -> tuple[float, float] | None:
    """Return (representative pixel side, pixels/mm) for validated sides."""
    sides = np.asarray(side_lengths, dtype=np.float64).reshape(-1)
    if marker_size_mm <= 0 or sides.size != 4 or not np.isfinite(sides).all() or np.any(sides <= 0):
        return None
    mean_side = float(sides.mean())
    if mean_side < min_marker_side_px or sides.max() / mean_side - 1.0 > max_side_variation_ratio:
        return None
    pixels_per_mm = mean_side / marker_size_mm
    return round(mean_side, 2), round(pixels_per_mm, 6)


def detect_aruco_calibration(
    image: np.ndarray,
    marker_size_mm: float = 50.0,
    dictionary_name: str = "DICT_4X4_50",
    min_marker_side_px: float = 20.0,
    max_side_variation_ratio: float = 0.25,
) -> CalibrationResult:
    """Detect one valid marker and derive scale for this image only."""
    if marker_size_mm <= 0:
        return _failed(marker_size_mm, "invalid_marker_size")
    if not isinstance(image, np.ndarray) or image.ndim != 3:
        return _failed(marker_size_mm, "invalid_image")

    aruco = getattr(cv2, "aruco", None)
    if aruco is None:
        return _failed(marker_size_mm, "aruco_unavailable")
    dictionary_id = getattr(aruco, dictionary_name, None)
    if dictionary_id is None:
        return _failed(marker_size_mm, "dictionary_unavailable")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dictionary = aruco.getPredefinedDictionary(dictionary_id)
    parameters_factory = getattr(aruco, "DetectorParameters", None)
    parameters = parameters_factory() if parameters_factory else aruco.DetectorParameters_create()
    if hasattr(aruco, "ArucoDetector"):
        corners, ids, _ = aruco.ArucoDetector(dictionary, parameters).detectMarkers(gray)
    else:  # OpenCV 4.6 compatibility
        corners, ids, _ = aruco.detectMarkers(gray, dictionary, parameters=parameters)
    if ids is None or not corners:
        return _failed(marker_size_mm, "marker_not_detected")

    for marker_corners, marker_id in zip(corners, ids.flatten().tolist()):
        points = np.asarray(marker_corners, dtype=np.float64).reshape(4, 2)
        if not np.isfinite(points).all():
            continue
        side_lengths = np.array(
            [hypot(*(points[(index + 1) % 4] - points[index])) for index in range(4)],
            dtype=np.float64,
        )
        scale = calculate_marker_scale(side_lengths, marker_size_mm, min_marker_side_px, max_side_variation_ratio)
        if scale is None:
            continue
        marker_pixel_size, pixels_per_mm = scale
        return CalibrationResult(
            calibrated=True,
            marker_detected=True,
            marker_id=int(marker_id),
            marker_size_mm=float(marker_size_mm),
            marker_pixel_size=marker_pixel_size,
            pixels_per_mm=pixels_per_mm,
            calibration_status="calibrated",
            calibration_quality="valid",
            corners=points,
        )

    return _failed(marker_size_mm, "marker_geometry_invalid_or_too_small", marker_detected=True)


def convert_measurement_to_physical(measurement, calibration: CalibrationResult) -> dict:
    """Return additive physical values; never fabricate values when uncalibrated."""
    result = {
        "length_mm": None,
        "length_cm": None,
        "width_mm": None,
        "width_cm": None,
        "max_width_mm": None,
        "max_width_cm": None,
        "area_mm2": None,
        "area_cm2": None,
    }
    if not calibration.calibrated or not calibration.pixels_per_mm:
        return result
    scale = calibration.pixels_per_mm
    result.update(
        length_mm=round(measurement.length_px / scale, 3),
        length_cm=round(measurement.length_px / scale / 10.0, 4),
        width_mm=round(measurement.width_px / scale, 3),
        width_cm=round(measurement.width_px / scale / 10.0, 4),
        max_width_mm=round(measurement.max_width_px / scale, 3),
        max_width_cm=round(measurement.max_width_px / scale / 10.0, 4),
        area_mm2=round(measurement.area_px2 / (scale * scale), 3),
        area_cm2=round(measurement.area_px2 / (scale * scale) / 100.0, 4),
    )
    return result


def draw_calibration_overlay(image: np.ndarray, calibration: CalibrationResult) -> np.ndarray:
    """Draw marker and scale information without replacing the detection overlay."""
    overlay = image.copy()
    if calibration.corners is not None:
        points = np.round(calibration.corners).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(overlay, [points], True, (44, 190, 92), 3)
        for index, point in enumerate(points.reshape(4, 2)):
            cv2.circle(overlay, tuple(point), 5, (255, 220, 70), -1)
            cv2.putText(overlay, str(index + 1), tuple(point + (6, -6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 220, 70), 2)
        label = f"ArUco {calibration.marker_id} | {calibration.pixels_per_mm:.3f} px/mm"
    else:
        label = f"ArUco marker: {calibration.calibration_status}"
    cv2.putText(overlay, label, (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (44, 190, 92), 2)
    return overlay
