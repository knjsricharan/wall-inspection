import numpy as np

from backend.services.calibration_service import CalibrationResult, calculate_marker_scale, convert_measurement_to_physical, detect_aruco_calibration
from backend.services.condition_service import ConditionThresholds, assess_condition
from backend.services.measurement_service import CrackMeasurement


def _measurement(length=50.0, width=1.0, max_width=1.0, area=100):
    return CrackMeasurement(length, width, max_width, area, 0.0)


def _calibration(pixels_per_mm=10.0):
    return CalibrationResult(True, True, 7, 50.0, pixels_per_mm * 50.0, pixels_per_mm, "calibrated", "valid")


def test_physical_conversion_preserves_pixel_scale_math():
    physical = convert_measurement_to_physical(_measurement(100, 20, 30, 400), _calibration(10))
    assert physical["length_mm"] == 10.0
    assert physical["length_cm"] == 1.0
    assert physical["max_width_mm"] == 3.0
    assert physical["area_mm2"] == 4.0
    assert physical["area_cm2"] == 0.04


def test_known_marker_side_size_returns_pixels_per_mm():
    assert calculate_marker_scale(np.array([500, 500, 500, 500]), 50.0) == (500.0, 10.0)


def test_invalid_and_too_small_marker_geometry_fails_safely():
    assert calculate_marker_scale(np.array([500, 500, 50, 500]), 50.0) is None
    assert calculate_marker_scale(np.array([10, 10, 10, 10]), 50.0) is None


def test_uncalibrated_conversion_returns_no_fabricated_physical_values():
    calibration = detect_aruco_calibration(np.zeros((100, 100, 3), dtype=np.uint8), marker_size_mm=50)
    assert calibration.calibrated is False
    assert calibration.marker_detected is False
    assert convert_measurement_to_physical(_measurement(), calibration)["length_mm"] is None


def test_condition_rules_cover_mild_moderate_and_severe():
    thresholds = ConditionThresholds(width_moderate=1, width_severe=3, area_moderate=500, area_severe=2000, length_moderate=100, length_severe=500)
    mild = assess_condition([_measurement(20, 0.5, 0.5, 50)], [0.95], True, thresholds, [{"length_mm": 20, "max_width_mm": 0.5, "area_mm2": 50}])
    moderate = assess_condition([_measurement(200, 2, 2, 700)], [0.7], True, thresholds, [{"length_mm": 200, "max_width_mm": 2, "area_mm2": 700}])
    severe = assess_condition([_measurement(700, 4, 4, 3000)], [0.4], True, thresholds, [{"length_mm": 700, "max_width_mm": 4, "area_mm2": 3000}])
    assert mild.condition == "Mild"
    assert moderate.condition == "Moderate"
    assert severe.condition == "Severe"


def test_uncalibrated_assessment_is_explicitly_preliminary():
    assessment = assess_condition([_measurement(120, 4, 4, 1200)], [0.7], False)
    assert assessment.preliminary is True
    assert assessment.calibrated is False
    assert assessment.threshold_configuration["mode"] == "pixel_preliminary"


def test_condition_score_is_inverse_damage_score_and_bounded():
    thresholds = ConditionThresholds(width_moderate=3, width_severe=10, area_moderate=1000, area_severe=5000, length_moderate=100, length_severe=500)
    low_damage = assess_condition([_measurement(10, 0.5, 1, 10)], [0.95], False, thresholds)
    moderate_damage = assess_condition([_measurement(200, 2, 4, 1500)], [0.70], False, thresholds)
    high_damage = assess_condition([_measurement(700, 4, 12, 6000)], [0.40], False, thresholds)
    assert low_damage.condition_score > moderate_damage.condition_score > high_damage.condition_score
    assert 0.0 <= high_damage.condition_score <= 10.0
    assert 0.0 <= low_damage.condition_score <= 10.0
    assert low_damage.condition == "Mild"
    assert high_damage.condition == "Severe"


def test_high_condition_scores_are_not_severe():
    assessment = assess_condition([_measurement(10, 0.5, 1, 10)], [0.95], False)
    assert assessment.condition_score >= 7.5
    assert assessment.condition != "Severe"


def test_invalid_marker_size_fails_safely():
    result = detect_aruco_calibration(np.zeros((50, 50, 3), dtype=np.uint8), marker_size_mm=0)
    assert result.calibrated is False
    assert result.calibration_status == "invalid_marker_size"
