"""
Generate synthetic test images for quality-check regression testing.

Creates five test scenarios:
  1. wall_crack.jpg   — realistic wall texture with visible crack
  2. sharp_wall.jpg   — clean, well-lit wall texture
  3. blurry_wall.jpg  — heavily blurred wall (Gaussian σ=15)
  4. dark_wall.jpg    — very underexposed wall image
  5. corrupt.jpg      — random bytes (not a valid image)
"""

import os
import sys

import cv2
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _add_wall_texture(img: np.ndarray, seed: int = 42) -> np.ndarray:
    """Add a realistic stone/masonry-like texture to an image."""
    rng = np.random.RandomState(seed)
    h, w = img.shape[:2]

    # Base noise for stone texture
    noise = rng.randint(-25, 25, (h, w), dtype=np.int16)
    # Coarse grain — simulates large stone blocks
    coarse = cv2.resize(
        rng.randint(0, 30, (h // 16, w // 16), dtype=np.uint8),
        (w, h),
        interpolation=cv2.INTER_CUBIC,
    ).astype(np.int16)

    textured = img.astype(np.int16) + noise[:, :, np.newaxis] + coarse[:, :, np.newaxis]
    textured = np.clip(textured, 0, 255).astype(np.uint8)

    # Add some horizontal and vertical mortar lines
    for y in range(0, h, h // 6):
        y_jittered = y + rng.randint(-2, 3)
        y_jittered = max(0, min(h - 3, y_jittered))
        textured[y_jittered : y_jittered + 3, :] = np.clip(
            textured[y_jittered : y_jittered + 3, :].astype(np.int16) - 30, 0, 255
        ).astype(np.uint8)

    for x in range(0, w, w // 4):
        x_jittered = x + rng.randint(-3, 4)
        x_jittered = max(0, min(w - 3, x_jittered))
        textured[:, x_jittered : x_jittered + 3] = np.clip(
            textured[:, x_jittered : x_jittered + 3].astype(np.int16) - 25, 0, 255
        ).astype(np.uint8)

    return textured


def _add_crack(img: np.ndarray, seed: int = 99) -> np.ndarray:
    """Draw a visible crack pattern on the image."""
    rng = np.random.RandomState(seed)
    h, w = img.shape[:2]
    result = img.copy()

    # Main crack: jagged diagonal line
    points = []
    x, y = w // 4, 0
    while y < h:
        points.append((x, y))
        y += rng.randint(3, 8)
        x += rng.randint(-6, 7)
        x = max(0, min(w - 1, x))

    pts = np.array(points, dtype=np.int32)
    # Draw thick dark crack line
    cv2.polylines(result, [pts], isClosed=False, color=(30, 30, 30), thickness=3)
    # Draw thinner darker core
    cv2.polylines(result, [pts], isClosed=False, color=(10, 10, 10), thickness=1)

    # Secondary branch crack
    if len(points) > 20:
        branch_start_idx = len(points) // 3
        bx, by = points[branch_start_idx]
        branch_pts = [(bx, by)]
        for _ in range(30):
            by += rng.randint(2, 6)
            bx += rng.randint(1, 5)
            bx = min(w - 1, bx)
            by = min(h - 1, by)
            branch_pts.append((bx, by))
        bp = np.array(branch_pts, dtype=np.int32)
        cv2.polylines(result, [bp], isClosed=False, color=(35, 35, 35), thickness=2)

    return result


def generate_wall_crack(w: int = 800, h: int = 600) -> np.ndarray:
    """Wall image with visible crack — should PASS or WARNING, never FAIL."""
    # Base: warm stone color
    base = np.full((h, w, 3), [160, 150, 140], dtype=np.uint8)
    textured = _add_wall_texture(base, seed=42)
    cracked = _add_crack(textured, seed=99)
    return cracked


def generate_sharp_wall(w: int = 800, h: int = 600) -> np.ndarray:
    """Clean, sharp, well-lit wall — should PASS."""
    base = np.full((h, w, 3), [180, 175, 165], dtype=np.uint8)
    textured = _add_wall_texture(base, seed=77)
    return textured


def generate_blurry_wall(w: int = 800, h: int = 600) -> np.ndarray:
    """Heavily blurred wall — should FAIL."""
    sharp = generate_sharp_wall(w, h)
    blurred = cv2.GaussianBlur(sharp, (31, 31), 15)
    return blurred


def generate_dark_wall(w: int = 800, h: int = 600) -> np.ndarray:
    """Very dark / underexposed — should FAIL or WARNING depending on severity."""
    base = np.full((h, w, 3), [25, 22, 20], dtype=np.uint8)
    textured = _add_wall_texture(base, seed=55)
    # Ensure it stays very dark
    textured = np.clip(textured.astype(np.int16) - 15, 0, 255).astype(np.uint8)
    return textured


def generate_corrupt_file() -> bytes:
    """Random bytes — not a valid image."""
    rng = np.random.RandomState(123)
    return rng.bytes(4096)


if __name__ == "__main__":
    pairs = [
        ("wall_crack.jpg", generate_wall_crack()),
        ("sharp_wall.jpg", generate_sharp_wall()),
        ("blurry_wall.jpg", generate_blurry_wall()),
        ("dark_wall.jpg", generate_dark_wall()),
    ]
    for name, img in pairs:
        path = os.path.join(OUTPUT_DIR, name)
        cv2.imwrite(path, img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        bright = float(np.mean(gray))
        contrast = float(np.std(gray))
        h, w = img.shape[:2]
        print(f"{name:20s}  {w}x{h}  blur={blur:8.2f}  brightness={bright:6.2f}  contrast={contrast:5.2f}")

    corrupt_path = os.path.join(OUTPUT_DIR, "corrupt.jpg")
    with open(corrupt_path, "wb") as f:
        f.write(generate_corrupt_file())
    print(f"{'corrupt.jpg':20s}  (random bytes, 4096 B)")

    print(f"\nAll test images saved to: {OUTPUT_DIR}")
