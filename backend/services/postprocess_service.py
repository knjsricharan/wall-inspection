"""Conservative post-processing for YOLO segmentation masks."""

from dataclasses import dataclass

import cv2
import numpy as np

from backend.core.config import get_settings


@dataclass(frozen=True)
class MaskPostprocessConfig:
    min_region_area_px: int
    closing_kernel_size: int
    closing_iterations: int


def get_mask_postprocess_config() -> MaskPostprocessConfig:
    settings = get_settings()
    return MaskPostprocessConfig(
        min_region_area_px=max(0, settings.mask_min_region_area_px),
        closing_kernel_size=max(0, settings.mask_closing_kernel_size),
        closing_iterations=max(0, settings.mask_closing_iterations),
    )


def _as_binary_mask(mask: np.ndarray, image_shape: tuple[int, int] | None = None) -> np.ndarray:
    if not isinstance(mask, np.ndarray) or mask.ndim != 2:
        raise ValueError("Mask must be a two-dimensional array.")
    if mask.size == 0:
        raise ValueError("Mask must not be empty.")

    binary = (mask > 0).astype(np.uint8)
    if image_shape is not None:
        height, width = image_shape
        if height <= 0 or width <= 0:
            raise ValueError("Image dimensions must be positive.")
        if binary.shape != (height, width):
            binary = cv2.resize(binary, (width, height), interpolation=cv2.INTER_NEAREST)
            binary = (binary > 0).astype(np.uint8)
    return binary


def remove_small_regions(binary_mask: np.ndarray, min_region_area_px: int) -> np.ndarray:
    """Keep connected regions whose area is at least the configured threshold."""
    if min_region_area_px <= 1:
        return binary_mask.astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask.astype(np.uint8), connectivity=8)
    cleaned = np.zeros_like(binary_mask, dtype=np.uint8)
    for label in range(1, num_labels):
        if int(stats[label, cv2.CC_STAT_AREA]) >= min_region_area_px:
            cleaned[labels == label] = 1
    return cleaned


def close_small_gaps(binary_mask: np.ndarray, kernel_size: int, iterations: int) -> np.ndarray:
    """Apply a small morphological closing pass for narrow breaks."""
    if kernel_size < 2 or iterations < 1 or not np.any(binary_mask):
        return binary_mask.astype(np.uint8)
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    closed = cv2.morphologyEx(binary_mask.astype(np.uint8), cv2.MORPH_CLOSE, kernel, iterations=iterations)
    return (closed > 0).astype(np.uint8)


def postprocess_mask(
    raw_mask: np.ndarray,
    image_shape: tuple[int, int] | None = None,
    config: MaskPostprocessConfig | None = None,
) -> np.ndarray:
    """Return a measurement-ready binary mask without hiding unusual detections."""
    cfg = config or get_mask_postprocess_config()
    binary = _as_binary_mask(raw_mask, image_shape)
    cleaned = remove_small_regions(binary, cfg.min_region_area_px)
    cleaned = close_small_gaps(cleaned, cfg.closing_kernel_size, cfg.closing_iterations)
    cleaned = remove_small_regions(cleaned, cfg.min_region_area_px)
    return cleaned.astype(np.uint8)
