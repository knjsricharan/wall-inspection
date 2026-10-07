import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
