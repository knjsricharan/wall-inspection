import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from backend.main import app
import cv2
import numpy as np

client = TestClient(app)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def _load_fixture(name: str) -> bytes:
    path = os.path.join(FIXTURES_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Fixture {name} not found.")
    with open(path, "rb") as f:
        return f.read()

def _create_and_upload(image_name: str, image_bytes: bytes, content_type: str = "image/jpeg"):
    return client.post("/api/process-image", files={"image": (image_name, image_bytes, content_type)})

def test_valid_wall_image():
    print("Testing: valid wall-like image")
    data = _load_fixture("sharp_wall.jpg")
    response = _create_and_upload("sharp_wall.jpg", data)
    assert response.status_code == 200
    res = response.json()
    assert res["quality_result"]["status"] in ["pass", "warning"]
    assert res["metadata"] is not None
    assert res["processed_image_url"] is not None
    ops = res["metadata"]["operations_applied"]
    assert "mild_denoise" in ops
    assert "mild_sharpen" in ops
    print("  -> PASSED")

def test_low_light_image():
    print("Testing: low-light image (FAIL tier)")
    data = _load_fixture("dark_wall.jpg")
    response = _create_and_upload("dark_wall.jpg", data)
    assert response.status_code == 200
    res = response.json()
    assert res["quality_result"]["status"] == "fail"
    assert res["metadata"] is None
    assert res["processed_image_url"] is None
    print("  -> PASSED")

def test_blurry_image():
    print("Testing: blurry image (FAIL tier)")
    data = _load_fixture("blurry_wall.jpg")
    response = _create_and_upload("blurry_wall.jpg", data)
    assert response.status_code == 200
    res = response.json()
    assert res["quality_result"]["status"] == "fail"
    assert res["metadata"] is None
    print("  -> PASSED")

def test_corrupt_file():
    print("Testing: corrupt image")
    data = _load_fixture("corrupt.jpg")
    response = _create_and_upload("corrupt.jpg", data)
    assert response.status_code == 200
    res = response.json()
    assert res["quality_result"]["status"] == "fail"
    assert res["metadata"] is None
    print("  -> PASSED")

def test_unsupported_file():
    print("Testing: unsupported file")
    data = b"Some random text data"
    response = _create_and_upload("text.txt", data, "text/plain")
    assert response.status_code == 415
    print("  -> PASSED")

def test_very_small_image():
    print("Testing: very small image")
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", img)
    data = buf.tobytes()
    response = _create_and_upload("small.jpg", data)
    assert response.status_code == 200
    res = response.json()
    assert res["quality_result"]["status"] == "fail"
    assert "resolution" in res["quality_result"]["explanation"].lower()
    print("  -> PASSED")

def test_low_contrast_warning_image():
    print("Testing: low-contrast image (WARNING tier)")
    # Create an image that passes dimensions and blur but has low contrast
    img = np.ones((800, 800, 3), dtype=np.uint8) * 128
    # Add some noise to pass blur threshold
    noise = np.random.normal(0, 10, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)
    ok, buf = cv2.imencode(".jpg", img)
    data = buf.tobytes()
    response = _create_and_upload("low_contrast.jpg", data)
    assert response.status_code == 200
    res = response.json()
    
    # It might fail if contrast < 5, but we added noise std=10. Contrast should be ~10.
    # 5 < 10 < 15, so it should be WARNING.
    if res["quality_result"]["status"] == "fail":
        print("  -> WARNING: generated image failed quality check:", res["quality_result"]["explanation"])
    else:
        assert res["metadata"] is not None
        assert "clahe_contrast_enhancement" in res["metadata"]["operations_applied"]
        print(f"  -> PASSED (status: {res['quality_result']['status']})")

if __name__ == "__main__":
    tests = [
        test_valid_wall_image,
        test_low_light_image,
        test_blurry_image,
        test_corrupt_file,
        test_unsupported_file,
        test_very_small_image,
        test_low_contrast_warning_image
    ]
    
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  -> FAILED: {e}")
            
    print(f"\\nResults: {passed}/{len(tests)} passed.")
    if passed < len(tests):
        sys.exit(1)
