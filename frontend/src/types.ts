// API response types matching backend Pydantic schemas

export type QualityStatus = 'pass' | 'warning' | 'fail'

export interface QualityMetrics {
  width: number
  height: number
  blur_score: number
  brightness_mean: number
  contrast_std: number
  file_size_mb: number
}

export interface QualityCheckResponse {
  status: QualityStatus
  metrics: QualityMetrics
  explanation: string
  recommendation: string
}

export interface HealthResponse {
  status: string
  version: string
  supabase_connected: boolean
  supabase_note: string | null
}

export interface ProcessMetadata {
  operations_applied: string[]
  original_size: number[]
  processed_size: number[]
}

export interface ProcessResponse {
  quality_result: QualityCheckResponse
  original_image_url: string
  processed_image_url: string | null
  metadata: ProcessMetadata | null
}

export interface BoundingBox {
  x1: number
  y1: number
  x2: number
  y2: number
}

export interface SegmentationMask {
  polygon: number[][]
  mask_url: string
  cleaned_mask_url: string | null
}

export interface Detection {
  detection_id: number | null
  class_id: number
  class_name: string
  confidence: number
  bounding_box: BoundingBox
  segmentation_mask: SegmentationMask
  length_px: number | null
  width_px: number | null
  max_width_px: number | null
  area_px2: number | null
  orientation_deg: number | null
  measurement_unit: string | null
  calibrated: boolean | null
  length_mm: number | null
  length_cm: number | null
  width_mm: number | null
  width_cm: number | null
  max_width_mm: number | null
  max_width_cm: number | null
  area_mm2: number | null
  area_cm2: number | null
}

export interface MeasurementSummary {
  detected_cracks: number
  total_area_px2: number
  total_length_px: number
  max_width_px: number
  measurement_unit: string
  calibrated: boolean
  total_area_mm2: number | null
  total_area_cm2: number | null
  total_length_mm: number | null
  total_length_cm: number | null
  max_width_mm: number | null
  max_width_cm: number | null
}

export interface CalibrationInfo {
  marker_detected: boolean
  marker_id: number | null
  marker_size_mm: number
  marker_pixel_size: number | null
  pixels_per_mm: number | null
  calibrated: boolean
  measurement_unit: string
  calibration_status: string
  calibration_quality: string
}

export interface ConditionAssessment {
  condition: string
  condition_score: number
  calibrated: boolean
  measurement_mode: string
  preliminary: boolean
  assessment_type: string
  threshold_profile: string
  threshold_configuration: Record<string, number | boolean | string>
  basis: string[]
  reasons: string[]
}

export interface InferenceResponse {
  status: 'completed' | 'model_not_available'
  message: string
  model_path: string
  overlay_image_url: string | null
  measurement_overlay_url: string | null
  measurement_summary: MeasurementSummary | null
  calibration: CalibrationInfo | null
  calibration_overlay_url: string | null
  condition_assessment: ConditionAssessment | null
  detections: Detection[]
}

export interface ReportResponse {
  status: string
  report_id: string
  docx_url: string
  pdf_url: string
  png_url: string
  message: string
}
