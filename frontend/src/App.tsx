import { useState, useRef, useCallback, useEffect } from 'react'
import type { QualityCheckResponse, HealthResponse, QualityStatus, ProcessResponse } from './types'

const API_BASE = '/api'

// --- Health indicator ---

function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(setHealth)
      .catch(() => setError('Backend unreachable'))
  }, [])

  if (error) {
    return (
      <div className="health-row">
        <span className="health-dot health-dot--error" />
        {error}
      </div>
    )
  }

  if (!health) {
    return (
      <div className="health-row">
        <div className="spinner" style={{ marginRight: '0.5rem', width: '8px', height: '8px' }} />
        Connecting to backend...
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <div className="health-row">
        <span className="health-dot health-dot--ok" />
        Backend v{health.version} — online
      </div>
      <div className="health-row">
        <span className={`health-dot ${health.supabase_connected ? 'health-dot--ok' : 'health-dot--error'}`} />
        Supabase: {health.supabase_connected ? 'connected' : 'not configured'}
        {health.supabase_note && !health.supabase_connected && (
          <span style={{ marginLeft: '6px', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
            ({health.supabase_note})
          </span>
        )}
      </div>
    </div>
  )
}

// --- Status badge ---

function StatusBadge({ status }: { status: QualityStatus }) {
  const label = status.toUpperCase()
  const cls = `status-badge status-badge--${status}`
  return <span className={cls}>{label}</span>
}

// --- Metric tile ---

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric-item">
      <div className="metric-item__label">{label}</div>
      <div className="metric-item__value">{value}</div>
    </div>
  )
}

// --- Upload icon (SVG) ---

function UploadIcon() {
  return (
    <svg
      className="upload-area__icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )
}

// --- Main App ---

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ProcessResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFile = useCallback((file: File) => {
    const allowed = ['image/jpeg', 'image/jpg', 'image/png']
    if (!allowed.includes(file.type)) {
      setError('Only JPG and PNG images are accepted.')
      return
    }
    setSelectedFile(file)
    setResult(null)
    setError(null)
    const url = URL.createObjectURL(file)
    setPreviewUrl(prev => { if (prev) URL.revokeObjectURL(prev); return url })
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => setDragOver(false)

  const clearSelection = () => {
    setSelectedFile(null)
    setResult(null)
    setError(null)
    if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null) }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const runProcessing = async () => {
    if (!selectedFile) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const formData = new FormData()
      formData.append('image', selectedFile)

      const response = await fetch(`${API_BASE}/process-image`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}))
        throw new Error(detail?.detail ?? `Server error ${response.status}`)
      }

      const data: ProcessResponse = await response.json()
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header__inner">
          <div>
            <div className="app-header__title">AWIS-HM</div>
            <div className="app-header__subtitle">
              AI-Based Wall Inspection System for Heritage Masonry
            </div>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="page-container">

          {/* System status */}
          <div className="card">
            <div className="card__title">System Status</div>
            <HealthStatus />
          </div>

          {/* Image upload */}
          <div className="card">
            <div className="card__title">Image Upload</div>

            {!selectedFile ? (
              <div
                className={`upload-area${dragOver ? ' upload-area--drag-over' : ''}`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                aria-label="Upload image"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && fileInputRef.current?.click()}
              >
                <label className="upload-area__label" htmlFor="image-upload">
                  <UploadIcon />
                  <span className="upload-area__primary">
                    Select or drop an image
                  </span>
                  <span className="upload-area__secondary">
                    JPG or PNG, up to 20 MB
                  </span>
                </label>
                <input
                  id="image-upload"
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/jpg,image/png"
                  onChange={handleInputChange}
                  style={{ display: 'none' }}
                />
              </div>
            ) : (
              <div className="image-preview">
                <img
                  src={previewUrl ?? ''}
                  alt="Selected wall image"
                  className="image-preview__img"
                />
                <div className="image-preview__filename">
                  {selectedFile.name} &mdash; {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <button
                    id="btn-process-image"
                    className="btn btn--primary"
                    onClick={runProcessing}
                    disabled={loading}
                  >
                    {loading ? <><div className="spinner" />Processing...</> : 'Process Image'}
                  </button>
                  <button
                    id="btn-clear"
                    className="btn btn--secondary"
                    onClick={clearSelection}
                    disabled={loading}
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="error-message" role="alert">
              {error}
            </div>
          )}

          {/* Quality check result */}
          {result && (
            <div className="card" id="quality-result-card">
              <div className="card__title">Quality Check Result</div>
              <div className="quality-result">
                <div className="quality-result__header">
                  <StatusBadge status={result.quality_result.status} />
                </div>
                <p className="quality-result__explanation">{result.quality_result.explanation}</p>
                <div className="quality-result__recommendation">{result.quality_result.recommendation}</div>
                <div className="metrics-grid">
                  <MetricItem label="Width" value={`${result.quality_result.metrics.width} px`} />
                  <MetricItem label="Height" value={`${result.quality_result.metrics.height} px`} />
                  <MetricItem label="Blur score" value={result.quality_result.metrics.blur_score.toFixed(1)} />
                  <MetricItem label="Brightness" value={result.quality_result.metrics.brightness_mean.toFixed(1)} />
                  <MetricItem label="Contrast" value={result.quality_result.metrics.contrast_std.toFixed(1)} />
                  <MetricItem label="File size" value={`${result.quality_result.metrics.file_size_mb.toFixed(2)} MB`} />
                </div>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
                  Note: quality thresholds are configurable provisional values and are not scientifically validated limits.
                </p>
              </div>
            </div>
          )}

          {/* Processing result */}
          {result?.metadata && result?.processed_image_url && (
            <div className="card" id="process-result-card">
              <div className="card__title">Processing Result</div>
              <div className="process-result">
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                  <div style={{ flex: 1, minWidth: '300px' }}>
                    <strong>Original</strong>
                    <img src={API_BASE.replace('/api', '') + result.original_image_url} alt="Original" style={{ width: '100%', borderRadius: '4px', marginTop: '0.5rem' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: '300px' }}>
                    <strong>Processed</strong>
                    <img src={API_BASE.replace('/api', '') + result.processed_image_url} alt="Processed" style={{ width: '100%', borderRadius: '4px', marginTop: '0.5rem' }} />
                  </div>
                </div>
                <div style={{ marginTop: '1rem' }}>
                  <strong>Applied Operations:</strong>
                  <ul>
                    {result.metadata.operations_applied.map((op, idx) => (
                      <li key={idx} style={{ fontFamily: 'monospace' }}>{op}</li>
                    ))}
                  </ul>
                  <div style={{ fontSize: 'var(--font-size-sm)', marginTop: '0.5rem' }}>
                    Original Size: {result.metadata.original_size[0]}x{result.metadata.original_size[1]} | 
                    Processed Size: {result.metadata.processed_size[0]}x{result.metadata.processed_size[1]}
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </>
  )
}
