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
