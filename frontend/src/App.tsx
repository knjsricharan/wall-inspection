import { useCallback, useEffect, useRef, useState } from 'react'
import type { HealthResponse, InferenceResponse, ProcessResponse, QualityStatus, ReportResponse } from './types'

const API_BASE = '/api'
const PROJECT_TITLE = 'AI-Based Wall Inspection System for Heritage Masonry'
type View = 'home' | 'setup' | 'quality' | 'processing' | 'results'
type ProcessingPhase = 'idle' | 'quality' | 'detection'
const workflowSteps: Array<{ id: View; label: string; number: string }> = [
  { id: 'setup', label: 'Setup', number: '01' },
  { id: 'quality', label: 'Quality Check', number: '02' },
  { id: 'processing', label: 'Detection', number: '03' },
  { id: 'results', label: 'Results', number: '04' },
]

function StatusBadge({ status }: { status: QualityStatus }) {
  return <span className={'status-badge status-badge--' + status}>{status.toUpperCase()}</span>
}
function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [offline, setOffline] = useState(false)
  useEffect(() => {
    fetch(API_BASE + '/health')
      .then(response => { if (!response.ok) throw new Error('Backend unavailable'); return response.json() })
      .then(setHealth).catch(() => setOffline(true))
  }, [])
  if (offline) return <span className="system-status system-status--offline">Backend unavailable</span>
  if (!health) return <span className="system-status">Checking backend</span>
  return <span className="system-status system-status--online">Backend online · v{health.version}</span>
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return <div className="metric-item"><span>{label}</span><strong>{value}</strong></div>
}
function formatOptional(value: number | null | undefined, suffix: string, digits = 1) {
  return typeof value === 'number' ? value.toFixed(digits) + ' ' + suffix : 'Not returned'
}
function UploadIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} aria-hidden="true"><path d="M20 16.5v2A2.5 2.5 0 0 1 17.5 21h-11A2.5 2.5 0 0 1 4 18.5v-2" /><path d="m8.5 9.5 3.5-3.5 3.5 3.5M12 6v10" /></svg>
}
function ArrowIcon() {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
}

export default function App() {
  const [view, setView] = useState<View>('home')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [loading, setLoading] = useState(false)
  const [phase, setPhase] = useState<ProcessingPhase>('idle')
  const [result, setResult] = useState<ProcessResponse | null>(null)
  const [inference, setInference] = useState<InferenceResponse | null>(null)
  const [report, setReport] = useState<ReportResponse | null>(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const resetInspection = useCallback((nextView: View = 'home') => {
    setSelectedFile(null); setResult(null); setInference(null); setReport(null); setError(null); setPhase('idle')
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    setView(nextView)
  }, [previewUrl])

  const handleFile = useCallback((file: File) => {
    if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
      setError('Only JPG and PNG images are accepted. Choose another image to continue.')
      return
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(current => { if (current) URL.revokeObjectURL(current); return url })
    setSelectedFile(file); setResult(null); setInference(null); setReport(null); setError(null); setPhase('idle'); setView('setup')
  }, [])

  const runProcessing = async () => {
    if (!selectedFile) { setError('Choose an image before starting the inspection.'); return }
    setLoading(true); setError(null); setResult(null); setInference(null); setReport(null); setPhase('quality'); setView('processing')
    try {
      const formData = new FormData()
      formData.append('image', selectedFile)
      const processResponse = await fetch(API_BASE + '/process-image', { method: 'POST', body: formData })
      if (!processResponse.ok) {
        const detail = await processResponse.json().catch(() => ({}))
        throw new Error(detail?.detail ?? ('Server error ' + processResponse.status))
      }
      const processData: ProcessResponse = await processResponse.json()
      setResult(processData)
      if (!processData.processed_image_url) { setView('quality'); return }
      setPhase('detection')
      const inferenceResponse = await fetch(API_BASE + '/run-inference', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ processed_image_url: processData.processed_image_url }),
      })
      if (!inferenceResponse.ok) {
        const detail = await inferenceResponse.json().catch(() => ({}))
        throw new Error(detail?.detail ?? ('Inference server error ' + inferenceResponse.status))
      }
      setInference(await inferenceResponse.json())
      setView('results')
    } catch (caughtError: unknown) {
      setError(caughtError instanceof Error ? caughtError.message : 'An unexpected error occurred.')
      setView('setup')
    } finally { setLoading(false); setPhase('idle') }
  }

  const generateReport = async () => {
    if (!result || !inference || inference.status !== 'completed') return
    setReportLoading(true); setError(null)
    try {
      const response = await fetch(API_BASE + '/generate-report', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_reference: selectedFile?.name ?? result.original_image_url,
          original_image_url: result.original_image_url,
          processed_image_url: result.processed_image_url,
          quality_status: result.quality_result.status,
          processing_status: 'completed',
          inference,
        }),
      })
      if (!response.ok) {
        const detail = await response.json().catch(() => ({}))
        throw new Error(detail?.detail ?? ('Report server error ' + response.status))
      }
      setReport(await response.json())
    } catch (caughtError: unknown) {
      setError(caughtError instanceof Error ? caughtError.message : 'Report generation failed.')
    } finally { setReportLoading(false) }
  }

  const imageUrl = (url: string) => API_BASE.replace('/api', '') + url
  const qualityFailed = result?.quality_result.status === 'fail'
  const canVisit = (target: View) => target === 'home' || target === 'setup'
    || (target === 'quality' && Boolean(result))
    || (target === 'processing' && loading)
    || (target === 'results' && Boolean(result && inference))
  const stageClass = (target: View) => {
    const complete = (target === 'setup' && Boolean(selectedFile)) || (target === 'quality' && Boolean(result))
      || (target === 'processing' && Boolean(inference)) || (target === 'results' && view === 'results')
    return 'workflow-nav__button' + (view === target ? ' is-active' : '') + (complete ? ' is-complete' : '')
  }

  const workflow = <nav className="workflow-nav" aria-label="Inspection workflow">{workflowSteps.map((step, index) => (
    <div className="workflow-nav__item" key={step.id}>
      <button className={stageClass(step.id)} type="button" disabled={!canVisit(step.id)} onClick={() => setView(step.id)}><span>{stageClass(step.id).includes('is-complete') ? '✓' : step.number}</span>{step.label}</button>
      {index < workflowSteps.length - 1 && <i className="workflow-nav__line" aria-hidden="true" />}
    </div>
  ))}</nav>

  const home = <section className="home-page">
    <div className="hero-panel">
      <div className="eyebrow">Visible-surface inspection assistance</div>
      <h1>Inspect masonry images with a clear, evidence-led workflow.</h1>
      <p>Upload a wall image, review its suitability, and view segmentation detections from the configured local model.</p>
      <div className="hero-panel__actions"><button className="btn btn--primary" type="button" onClick={() => resetInspection('setup')}>Start new inspection <ArrowIcon /></button><HealthStatus /></div>
    </div>
    <div className="home-grid">
      <section className="info-panel"><div className="section-kicker">Current workflow</div><h2>From image to visible detection output</h2><ol className="workflow-list">
        <li><b>1</b><span><strong>Upload</strong> JPG or PNG wall imagery.</span></li><li><b>2</b><span><strong>Quality check</strong> Review blur, exposure, contrast, and resolution.</span></li><li><b>3</b><span><strong>Enhancement</strong> Process usable imagery only.</span></li><li><b>4</b><span><strong>Detection</strong> View segmentation overlay and model output.</span></li>
      </ol></section>
      <aside className="scope-panel"><div className="section-kicker">Scope</div><p>Results describe visible image features only. They do not assess hidden damage or certify structural safety.</p></aside>
    </div>
  </section>

  const setup = <section className="page-section">
    <div className="page-heading"><div><div className="eyebrow">New inspection</div><h1>Image upload and setup</h1><p>Select a clear image of the wall surface to begin the inspection workflow.</p></div><button className="text-button" type="button" onClick={() => resetInspection('home')}>Back to dashboard</button></div>
    {error && <div className="error-message" role="alert">{error}</div>}
    <div className="upload-panel">
      {!selectedFile ? <div className={'upload-area' + (dragOver ? ' upload-area--drag-over' : '')} onDrop={event => {
        event.preventDefault(); setDragOver(false); const file = event.dataTransfer.files[0]; if (file) handleFile(file)
      }} onDragOver={event => { event.preventDefault(); setDragOver(true) }} onDragLeave={() => setDragOver(false)} onClick={() => fileInputRef.current?.click()} role="button" aria-label="Select image to inspect" tabIndex={0} onKeyDown={event => event.key === 'Enter' && fileInputRef.current?.click()}>
        <UploadIcon /><strong>Select or drop an image</strong><span>JPG or PNG · up to 20 MB</span>
        <input ref={fileInputRef} type="file" accept="image/jpeg,image/jpg,image/png" onChange={event => { const file = event.target.files?.[0]; if (file) handleFile(file) }} hidden />
      </div> : <div className="selected-image">
        <img src={previewUrl ?? ''} alt="Selected wall image" /><div className="selected-image__details"><div><div className="section-kicker">Selected image</div><h2>{selectedFile.name}</h2><p>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB · Ready for quality assessment</p></div><div className="button-row"><button className="btn btn--primary" type="button" onClick={runProcessing} disabled={loading}>Begin inspection <ArrowIcon /></button><button className="btn btn--secondary" type="button" onClick={() => resetInspection('setup')} disabled={loading}>Clear image</button></div></div>
      </div>}
    </div>
    <p className="helper-text">The quality gate reviews the uploaded image before any enhancement or model inference is performed.</p>
  </section>

  const quality = result && <section className="page-section">
    <div className="page-heading"><div><div className="eyebrow">Inspection quality</div><h1>Quality check result</h1><p>The quality check evaluates the uploaded image; it does not modify it.</p></div><div className="button-row"><button className="text-button" type="button" onClick={() => setView('setup')}>Back to setup</button><button className="text-button" type="button" onClick={() => resetInspection('setup')}>Choose another image</button></div></div>
    <section className="quality-summary"><div className="quality-summary__status"><StatusBadge status={result.quality_result.status} /><div><h2>{qualityFailed ? 'A new image is needed' : 'Image can continue through the workflow'}</h2><p>{result.quality_result.explanation}</p></div></div><div className="quality-summary__recommendation">{result.quality_result.recommendation}</div></section>
    <div className="metrics-grid"><MetricItem label="Resolution" value={result.quality_result.metrics.width + ' × ' + result.quality_result.metrics.height + ' px'} /><MetricItem label="Blur score" value={result.quality_result.metrics.blur_score.toFixed(1)} /><MetricItem label="Brightness" value={result.quality_result.metrics.brightness_mean.toFixed(1)} /><MetricItem label="Contrast" value={result.quality_result.metrics.contrast_std.toFixed(1)} /></div>
    <div className="page-actions">{qualityFailed ? <button className="btn btn--primary" type="button" onClick={() => resetInspection('setup')}>Choose another image <ArrowIcon /></button> : inference ? <button className="btn btn--primary" type="button" onClick={() => setView('results')}>View detection results <ArrowIcon /></button> : <button className="btn btn--primary" type="button" onClick={runProcessing}>Run detection <ArrowIcon /></button>}</div>
  </section>

  const processing = <section className="page-section processing-page">
    <div className="page-heading"><div><div className="eyebrow">Inspection in progress</div><h1>Processing and detection</h1><p>Completed stages are shown as soon as the application receives their result.</p></div></div>
      <div className="processing-track" aria-live="polite">
      <div className={result ? 'is-complete' : phase === 'quality' ? 'is-active' : ''}><span>1</span><strong>Quality check</strong><small>{result ? 'Complete' : phase === 'quality' ? 'Running' : 'Waiting'}</small></div>
      <div className={result?.metadata ? 'is-complete' : ''}><span>2</span><strong>Enhancement</strong><small>{result?.metadata ? 'Complete' : 'Waiting'}</small></div>
      <div className={inference ? 'is-complete' : phase === 'detection' ? 'is-active' : ''}><span>3</span><strong>Detection and measurement</strong><small>{inference ? 'Complete' : phase === 'detection' ? 'Running' : 'Waiting'}</small></div>
    </div>
    <div className="processing-note"><div className="spinner" /><div><strong>{phase === 'detection' ? 'Running segmentation inference' : 'Reviewing image quality'}</strong><p>Please keep this page open while the current step completes.</p></div></div>
  </section>

  const results = result && inference && <section className="page-section">
    <div className="page-heading"><div><div className="eyebrow">Inspection output</div><h1>Segmentation results</h1><p>Review the processed image and model output. Results refer only to visible surface features in this image.</p></div><div className="button-row"><button className="text-button" type="button" onClick={() => setView('quality')}>Quality check</button><button className="text-button" type="button" onClick={() => resetInspection('setup')}>Start over</button></div></div>
    <section className="result-section"><div className="result-section__heading"><div><div className="section-kicker">Image review</div><h2>Original and processed image</h2></div></div><div className="image-comparison"><figure><img src={imageUrl(result.original_image_url)} alt="Original wall image" /><figcaption>Original image</figcaption></figure>{result.processed_image_url && <figure><img src={imageUrl(result.processed_image_url)} alt="Processed wall image" /><figcaption>Processed image</figcaption></figure>}</div>{result.metadata && <p className="operations-note">Applied operations: {result.metadata.operations_applied.join(', ')}.</p>}</section>
    <section className="result-section"><div className="result-section__heading"><div><div className="section-kicker">Detection output</div><h2>Segmentation overlay</h2></div></div>{inference.status === 'model_not_available' ? <div className="state-notice state-notice--warning"><strong>Model not available</strong><p>{inference.message}</p><code>{inference.model_path}</code></div> : <>{inference.overlay_image_url && <img className="inference-overlay" src={imageUrl(inference.overlay_image_url)} alt="Segmentation overlay" />}<div className="detection-summary"><strong>{inference.detections.length}</strong><span>{inference.detections.length === 1 ? 'detection returned' : 'detections returned'}</span><p>{inference.message}</p></div></>}</section>
    {inference.status === 'completed' && inference.measurement_summary && <section className="result-section"><div className="result-section__heading"><div><div className="section-kicker">Measurements</div><h2>Pixel crack measurements</h2></div></div><div className="metrics-grid measurement-grid"><MetricItem label="Detected cracks" value={String(inference.measurement_summary.detected_cracks)} /><MetricItem label="Total crack area" value={inference.measurement_summary.total_area_px2.toFixed(0) + ' px²'} /><MetricItem label="Total crack length" value={inference.measurement_summary.total_length_px.toFixed(1) + ' px'} /><MetricItem label="Maximum crack width" value={inference.measurement_summary.max_width_px.toFixed(1) + ' px'} /></div><p className="operations-note">Measurement mode: pixel. Physical dimensions are not used in the live assessment.</p>{inference.measurement_overlay_url && <figure className="measurement-figure"><img className="inference-overlay" src={imageUrl(inference.measurement_overlay_url)} alt="Measurement overlay" /><figcaption>Measurement and cleaned-mask overlay</figcaption></figure>}</section>}
    {inference.status === 'completed' && inference.condition_assessment && <section className="result-section"><div className="result-section__heading"><div><div className="section-kicker">Condition assessment</div><h2>Visible Surface Condition Assessment</h2></div><strong className="condition-badge">{inference.condition_assessment.condition}</strong></div><div className="metrics-grid measurement-grid"><MetricItem label="Condition score" value={inference.condition_assessment.condition_score.toFixed(1) + ' / 10'} /><MetricItem label="Measurement mode" value="Pixel-based" /></div><p className="assessment-factors">Assessment factors: Crack width · Crack area · Crack length · Detection confidence</p></section>}
    {inference.status === 'completed' && <section className="result-section report-section"><div className="result-section__heading"><div><div className="section-kicker">Report</div><h2>Automated inspection report</h2></div></div><p className="operations-note">Generate a report from this live pixel-based inspection. It contains no generated recommendations.</p><button className="btn btn--primary report-generate-button" type="button" onClick={generateReport} disabled={reportLoading}>{reportLoading ? 'Generating report' : 'Generate report'} <ArrowIcon /></button>{report && <div className="report-links"><a className="export-button" href={imageUrl(report.docx_url)} download>DOCX</a><a className="export-button" href={imageUrl(report.pdf_url)} download>PDF</a><a className="export-button" href={imageUrl(report.png_url)} download>PNG</a></div>}</section>}
    {inference.status === 'completed' && <section className="result-section"><div className="result-section__heading"><div><div className="section-kicker">Detection details</div><h2>Model detections</h2></div></div>{inference.detections.length === 0 ? <div className="state-notice"><strong>No detectable surface damage</strong><p>No damage was detected by the current model. This is not proof that the wall is defect-free.</p></div> : <div className="detections-table-wrap"><table className="detections-table"><thead><tr><th>Crack</th><th>Class</th><th>Confidence</th><th>Length</th><th>Width</th><th>Max width</th><th>Area</th><th>Orientation</th><th>Unit</th><th>Mask</th></tr></thead><tbody>{inference.detections.map((detection, index) => <tr key={detection.class_id + '-' + index}><td>{(detection.detection_id ?? index) + 1}</td><td>{detection.class_name}</td><td>{(detection.confidence * 100).toFixed(1)}%</td><td>{formatOptional(detection.length_px, 'px')}</td><td>{formatOptional(detection.width_px, 'px')}</td><td>{formatOptional(detection.max_width_px, 'px')}</td><td>{typeof detection.area_px2 === 'number' ? detection.area_px2.toFixed(0) + ' px²' : 'Not returned'}</td><td>{formatOptional(detection.orientation_deg, '°')}</td><td>pixel</td><td><a href={imageUrl(detection.segmentation_mask.cleaned_mask_url ?? detection.segmentation_mask.mask_url)} target="_blank" rel="noreferrer">Open mask</a></td></tr>)}</tbody></table></div>}</section>}
  </section>

  return <div className="app-shell">
    <header className="app-header"><div className="app-header__inner"><button className="brand" type="button" onClick={() => setView('home')} aria-label="Open dashboard"><span>{PROJECT_TITLE}</span></button><nav className="header-nav" aria-label="Primary navigation"><button type="button" className={view === 'home' ? 'is-active' : ''} onClick={() => setView('home')}>Dashboard</button><button type="button" className={view === 'setup' ? 'is-active' : ''} onClick={() => resetInspection('setup')}>New inspection</button></nav></div></header>
    <main className="app-main"><div className="page-container">{view !== 'home' && workflow}{view === 'home' && home}{view === 'setup' && setup}{view === 'quality' && quality}{view === 'processing' && processing}{view === 'results' && results}</div></main>
    <footer className="app-footer">By 23331A0599, 23331A05A0, 23331A05A4, 23331A05A9</footer>
  </div>
}
