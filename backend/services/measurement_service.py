"""Pixel-only crack measurement from cleaned binary masks."""

from dataclasses import dataclass
from math import atan2, degrees

import cv2
import numpy as np


@dataclass(frozen=True)
class CrackMeasurement:
    length_px: float
    width_px: float
    max_width_px: float
    area_px2: int
    orientation_deg: float | None
    measurement_unit: str = "pixel"
    calibrated: bool = False


def _validate_mask(mask: np.ndarray) -> np.ndarray:
    if not isinstance(mask, np.ndarray) or mask.ndim != 2:
        raise ValueError("Mask must be a two-dimensional array.")
    if mask.size == 0:
        raise ValueError("Mask must not be empty.")
    return (mask > 0).astype(np.uint8)


def _zhang_suen_skeleton(binary_mask: np.ndarray) -> np.ndarray:
    """Skeletonize a binary mask using Zhang-Suen thinning."""
    image = binary_mask.copy().astype(np.uint8)
    changing = True
    rows, cols = image.shape
    if rows < 3 or cols < 3:
        return image

    while changing:
        changing = False
        for step in (0, 1):
            to_remove: list[tuple[int, int]] = []
            for y in range(1, rows - 1):
                for x in range(1, cols - 1):
                    if image[y, x] == 0:
                        continue
                    p2 = image[y - 1, x]
                    p3 = image[y - 1, x + 1]
                    p4 = image[y, x + 1]
                    p5 = image[y + 1, x + 1]
                    p6 = image[y + 1, x]
                    p7 = image[y + 1, x - 1]
                    p8 = image[y, x - 1]
                    p9 = image[y - 1, x - 1]
                    neighbors = [p2, p3, p4, p5, p6, p7, p8, p9]
                    count = int(sum(neighbors))
                    transitions = sum(1 for i in range(8) if neighbors[i] == 0 and neighbors[(i + 1) % 8] == 1)
                    if count < 2 or count > 6 or transitions != 1:
                        continue
                    if step == 0:
                        condition = p2 * p4 * p6 == 0 and p4 * p6 * p8 == 0
                    else:
                        condition = p2 * p4 * p8 == 0 and p2 * p6 * p8 == 0
                    if condition:
                        to_remove.append((y, x))
            if to_remove:
                changing = True
                for y, x in to_remove:
                    image[y, x] = 0
    return image


def skeleton_length_px(skeleton: np.ndarray) -> float:
    """Estimate centerline length with horizontal/vertical and diagonal edges."""
    skel = (skeleton > 0).astype(np.uint8)
    length = 0.0
    # Count each 8-connected edge once by only looking forward.
    directions = ((0, 1, 1.0), (1, 0, 1.0), (1, 1, 2 ** 0.5), (1, -1, 2 ** 0.5))
    height, width = skel.shape
    for y in range(height):
        for x in range(width):
            if skel[y, x] == 0:
                continue
            for dy, dx, weight in directions:
                yy = y + dy
                xx = x + dx
                if 0 <= yy < height and 0 <= xx < width and skel[yy, xx]:
                    length += weight
    if length == 0.0 and np.any(skel):
        return 1.0
    return float(length)


def orientation_degrees(binary_mask: np.ndarray) -> float | None:
    ys, xs = np.nonzero(binary_mask)
    if len(xs) < 2:
        return None
    points = np.column_stack((xs.astype(np.float64), ys.astype(np.float64)))
    centered = points - points.mean(axis=0)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    vx, vy = vh[0]
    angle = degrees(atan2(vy, vx))
    if angle <= -90:
        angle += 180
    elif angle > 90:
        angle -= 180
    return round(float(angle), 2)


def measure_crack_mask(mask: np.ndarray) -> CrackMeasurement:
    """Calculate uncalibrated pixel measurements for a cleaned crack mask."""
    binary = _validate_mask(mask)
    area = int(np.count_nonzero(binary))
    if area == 0:
        return CrackMeasurement(
            length_px=0.0,
            width_px=0.0,
            max_width_px=0.0,
            area_px2=0,
            orientation_deg=None,
        )

    skeleton = _zhang_suen_skeleton(binary)
    length = skeleton_length_px(skeleton)
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    skeleton_distances = distance[skeleton.astype(bool)]
    if skeleton_distances.size:
        widths = skeleton_distances * 2.0
        representative_width = float(np.mean(widths))
        max_width = float(np.max(widths))
    else:
        representative_width = float(area / max(length, 1.0))
        max_width = representative_width

    return CrackMeasurement(
        length_px=round(float(length), 2),
        width_px=round(representative_width, 2),
        max_width_px=round(max_width, 2),
        area_px2=area,
        orientation_deg=orientation_degrees(binary),
    )


def summarize_measurements(measurements: list[CrackMeasurement]) -> dict[str, float | int | str | bool]:
    return {
        "detected_cracks": len(measurements),
        "total_area_px2": int(sum(item.area_px2 for item in measurements)),
        "total_length_px": round(float(sum(item.length_px for item in measurements)), 2),
        "max_width_px": round(float(max((item.max_width_px for item in measurements), default=0.0)), 2),
        "measurement_unit": "pixel",
        "calibrated": False,
    }
