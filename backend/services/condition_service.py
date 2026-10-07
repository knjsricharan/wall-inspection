"""Project-defined visible surface condition assessment rules."""

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ConditionThresholds:
    width_moderate: float = 1.0
    width_severe: float = 3.0
    area_moderate: float = 500.0
    area_severe: float = 2000.0
    length_moderate: float = 100.0
    length_severe: float = 500.0
    confidence_high: float = 0.75
    confidence_low: float = 0.50
    uncalibrated_supported: bool = True
    mild_min_score: float = 7.5
    moderate_min_score: float = 4.0


@dataclass(frozen=True)
class ConditionAssessment:
    condition: str
    condition_score: float
    calibrated: bool
    measurement_mode: str
    preliminary: bool
    assessment_type: str
    threshold_profile: str
    threshold_configuration: dict
    basis: list[str]
    reasons: list[str]


def _severity(value: float, moderate: float, severe: float) -> float:
    if value >= severe:
        return 3.0
    if value >= moderate:
        return 2.0
    return 0.5 if value > 0 else 0.0


def assess_condition(measurements: list, confidences: list[float], calibrated: bool, thresholds: ConditionThresholds | None = None, physical_values: list[dict] | None = None) -> ConditionAssessment:
    """Score visible surface damage, with explicit calibrated/uncalibrated modes."""
    config = thresholds or ConditionThresholds()
    profile = "physical_mm" if calibrated else "pixel_preliminary"
    if not calibrated and not config.uncalibrated_supported:
        return ConditionAssessment(
            condition="No detectable surface damage",
            condition_score=0.0,
            calibrated=False,
            measurement_mode="pixel",
            preliminary=True,
            assessment_type="visible_surface_condition",
            threshold_profile="project_defined",
            threshold_configuration={"mode": profile, **asdict(config)},
            basis=[],
            reasons=["Assessment unavailable without a valid image-specific scale reference."],
        )

    valid = [item for item in measurements if item is not None]
    basis = ["maximum crack width", "total crack area", "crack length", "detection confidence"]
    if not valid:
        return ConditionAssessment(
            condition="No detectable surface damage",
            condition_score=0.0,
            calibrated=calibrated,
            measurement_mode="mm" if calibrated else "pixel",
            preliminary=not calibrated,
            assessment_type="visible_surface_condition",
            threshold_profile="project_defined",
            threshold_configuration={"mode": profile, **asdict(config)},
            basis=[],
            reasons=["No damage was detected by the current model; this is not proof that the wall is defect-free."],
        )

    width = max(item.max_width_px for item in valid)
    area = sum(item.area_px2 for item in valid)
    length = sum(item.length_px for item in valid)
    if calibrated:
        # Thresholds are expressed in millimetres/mm² only for the calibrated profile.
        # Conversion is supplied by the caller through physical attributes.
        physical = physical_values or []
        width = max((item.get("max_width_mm") or 0.0 for item in physical), default=0.0)
        area = sum((item.get("area_mm2") or 0.0 for item in physical))
        length = sum((item.get("length_mm") or 0.0 for item in physical))
    width_score = _severity(width, config.width_moderate, config.width_severe)
    area_score = _severity(area, config.area_moderate, config.area_severe)
    length_score = _severity(length, config.length_moderate, config.length_severe)
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    confidence_score = 0.0 if average_confidence >= config.confidence_high else 1.0 if average_confidence >= config.confidence_low else 2.0
    damage_score = (width_score + area_score + length_score + confidence_score) / 12.0 * 10.0
    score = round(max(0.0, min(10.0, 10.0 - damage_score)), 2)
    condition = "Mild" if score >= config.mild_min_score else "Moderate" if score >= config.moderate_min_score else "Severe"
    reasons = []
    if width_score >= 2: reasons.append("Maximum crack width contributes to the assessment.")
    if area_score >= 2: reasons.append("Total crack area contributes to the assessment.")
    if length_score >= 2: reasons.append("Total crack length contributes to the assessment.")
    if confidence_score > 0: reasons.append("Detection confidence lowers certainty in the assessment.")
    if not reasons: reasons.append("Measured visible crack dimensions remain below the project-defined moderate thresholds.")
    return ConditionAssessment(
        condition=condition,
        condition_score=score,
        calibrated=calibrated,
        measurement_mode="mm" if calibrated else "pixel",
        preliminary=not calibrated,
        assessment_type="visible_surface_condition",
        threshold_profile="project_defined",
        threshold_configuration={"mode": profile, **asdict(config)},
        basis=basis,
        reasons=reasons,
    )
