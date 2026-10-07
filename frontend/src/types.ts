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
}

export interface Detection {
  class_id: number
  class_name: string
  confidence: number
  bounding_box: BoundingBox
  segmentation_mask: SegmentationMask
}

export interface InferenceResponse {
  status: 'completed' | 'model_not_available'
  message: string
  model_path: string
  overlay_image_url: string | null
  detections: Detection[]
}
