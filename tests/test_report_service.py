from types import SimpleNamespace

from PIL import Image

from backend.schemas.inference import (
    BoundingBox,
    ConditionAssessment,
    Detection,
    InferenceResponse,
    MeasurementSummary,
    SegmentationMask,
)
from backend.schemas.report import ReportRequest
from backend.services import report_service


def _request(tmp_path, detections=True):
    image_path = tmp_path / "wall.png"
    Image.new("RGB", (180, 120), "#d7d0c4").save(image_path)
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    overlay_path = upload_dir / "overlay.jpg"
    Image.new("RGB", (180, 120), "#8a5a45").save(overlay_path)
    inference = InferenceResponse(
        status="completed", message="Inference completed", model_path="models/best.pt",
        overlay_image_url="/uploads/overlay.jpg",
        measurement_overlay_url=None,
        measurement_summary=MeasurementSummary(detected_cracks=1 if detections else 0, total_area_px2=200 if detections else 0, total_length_px=40 if detections else 0, max_width_px=4 if detections else 0),
        condition_assessment=ConditionAssessment(condition="Moderate" if detections else "No detectable surface damage", condition_score=5.0 if detections else 0.0, calibrated=False, measurement_mode="pixel", preliminary=True, assessment_type="visible_surface_condition", threshold_profile="project_defined", threshold_configuration={}, basis=["maximum crack width"] if detections else [], reasons=["Maximum detected crack width"] if detections else ["No damage was detected by the current model; this is not proof that the wall is defect-free."]),
        detections=[Detection(detection_id=0, class_id=0, class_name="crack", confidence=0.9, bounding_box=BoundingBox(x1=1, y1=2, x2=50, y2=60), segmentation_mask=SegmentationMask(polygon=[[1, 2], [50, 60]], mask_url="/uploads/mask.png"), length_px=40, width_px=3, max_width_px=4, area_px2=200, orientation_deg=12, measurement_unit="pixel", calibrated=False)] if detections else [],
    )
    request = ReportRequest(image_reference="wall.png", original_image_url="/uploads/wall.png", processed_image_url=None, quality_status="pass", inference=inference)
    Image.open(image_path).save(upload_dir / "wall.png")
    return request, upload_dir


def test_report_generates_docx_pdf_png_without_physical_content(tmp_path, monkeypatch):
    request, upload_dir = _request(tmp_path)
    monkeypatch.setattr(report_service, "get_settings", lambda: SimpleNamespace(upload_dir=str(upload_dir)))
    output = report_service.generate_report(request)
    paths = [upload_dir / output["docx_url"].split("/uploads/")[1], upload_dir / output["pdf_url"].split("/uploads/")[1], upload_dir / output["png_url"].split("/uploads/")[1]]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
    assert b"calibration" not in paths[1].read_bytes().lower()
    assert b"rag" not in paths[1].read_bytes().lower()


def test_report_handles_no_detections(tmp_path, monkeypatch):
    request, upload_dir = _request(tmp_path, detections=False)
    monkeypatch.setattr(report_service, "get_settings", lambda: SimpleNamespace(upload_dir=str(upload_dir)))
    output = report_service.generate_report(request)
    assert output["report_id"].startswith("AWIS-")
    assert (upload_dir / output["png_url"].split("/uploads/")[1]).exists()
