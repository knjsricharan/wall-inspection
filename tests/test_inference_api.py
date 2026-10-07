import os
import sys
from types import SimpleNamespace

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import cv2
import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.inference_service import _load_model

client = TestClient(app)


def test_missing_model_returns_explicit_unavailable_state(monkeypatch, tmp_path):
    """Missing weights must never be represented as empty/fake predictions."""
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "missing-best.pt"))
    from backend.core.config import get_settings

    get_settings.cache_clear()
    _load_model.cache_clear()
    response = client.post("/api/run-inference", json={"processed_image_url": "/uploads/example.jpg"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "model_not_available"
    assert payload["detections"] == []
    assert payload["overlay_image_url"] is None
    assert "Model not available" in payload["message"]

    monkeypatch.delenv("MODEL_PATH")
    get_settings.cache_clear()


def test_rejects_url_outside_processed_uploads(monkeypatch, tmp_path):
    """The endpoint only accepts an image created by the local pipeline."""
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"placeholder")
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    from backend.core.config import get_settings

    get_settings.cache_clear()
    response = client.post("/api/run-inference", json={"processed_image_url": "/not-uploads/image.jpg"})

    assert response.status_code == 400
    assert "processing pipeline" in response.json()["detail"]

    monkeypatch.delenv("MODEL_PATH")
    get_settings.cache_clear()


class _FakeTensor:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value

    def tolist(self):
        return self.value

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class _FakeBox:
    cls = _FakeTensor(0)
    conf = _FakeTensor(0.91)
    xyxy = [_FakeTensor([5.0, 10.0, 35.0, 10.0])]


class _FakeModel:
    def predict(self, **kwargs):
        mask = np.zeros((50, 50), dtype=np.float32)
        cv2.line(mask, (5, 10), (35, 10), 1.0, 1)
        return [
            SimpleNamespace(
                masks=SimpleNamespace(data=_FakeTensor(np.array([mask]))),
                boxes=[_FakeBox()],
                names={0: "crack"},
            )
        ]


def test_inference_response_preserves_existing_fields_and_adds_measurements(monkeypatch, tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    image_path = upload_dir / "processed.jpg"
    cv2.imwrite(str(image_path), np.zeros((50, 50, 3), dtype=np.uint8))
    model_path = tmp_path / "best.pt"
    model_path.write_bytes(b"placeholder")

    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("MODEL_PATH", str(model_path))
    from backend.core.config import get_settings
    import backend.services.inference_service as inference_service

    get_settings.cache_clear()
    _load_model.cache_clear()
    monkeypatch.setattr(inference_service, "_load_model", lambda _path: _FakeModel())

    response = client.post("/api/run-inference", json={"processed_image_url": "/uploads/processed.jpg"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["overlay_image_url"]
    assert payload["measurement_overlay_url"]
    assert payload["measurement_summary"]["measurement_unit"] == "pixel"
    assert payload["measurement_summary"]["calibrated"] is False
    detection = payload["detections"][0]
    assert detection["class_name"] == "crack"
    assert detection["confidence"] == 0.91
    assert detection["bounding_box"] == {"x1": 5.0, "y1": 10.0, "x2": 35.0, "y2": 10.0}
    assert detection["segmentation_mask"]["mask_url"]
    assert detection["segmentation_mask"]["cleaned_mask_url"]
    assert detection["length_px"] > 0
    assert detection["area_px2"] > 0
    assert detection["measurement_unit"] == "pixel"
    assert detection["calibrated"] is False

    monkeypatch.delenv("UPLOAD_DIR")
    monkeypatch.delenv("MODEL_PATH")
    get_settings.cache_clear()
