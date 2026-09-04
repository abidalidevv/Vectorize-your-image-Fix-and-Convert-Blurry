import React, { useState } from 'react'
import { useAppStore } from '../store/appStore'
import {
  preprocessImage,
  quantizeImage,
  vectorizeImage,
  analyzeImage,
  exportSVG,
  exportPNG,
} from '../api/client'

type SectionId = 'image' | 'preprocess' | 'quantize' | 'vectorize'

function Section({ id, title, open, onToggle, children }: {
  id: SectionId; title: string; open: boolean
  onToggle: () => void; children: React.ReactNode
}) {
  return (
    <div className="panel-section">
      <div className="panel-section-header" onClick={onToggle}>
        <span className="panel-section-title">{title}</span>
        <span className={`panel-section-chevron ${open ? 'open' : ''}`}>▶</span>
      </div>
      {open && <div className="panel-section-content">{children}</div>}
    </div>
  )
}

function Slider({ label, value, min, max, step = 0.01, onChange, disabled = false }: {
  label: string; value: number; min: number; max: number
  step?: number; onChange: (v: number) => void; disabled?: boolean
}) {
  return (
    <div className="control-group">
      <div className="control-label">
        <span>{label}</span>
        <span className="value-display">{value.toFixed(step < 0.1 ? 2 : step < 1 ? 1 : 0)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        disabled={disabled}
      />
    </div>
  )
}

function Toggle({ label, value, onChange, disabled = false }: {
  label: string; value: boolean; onChange: (v: boolean) => void; disabled?: boolean
}) {
  return (
    <div className="toggle-row">
      <span className="toggle-label">{label}</span>
      <label className="toggle">
        <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />
        <div className="toggle-track">
          <div className="toggle-thumb" />
        </div>
      </label>
    </div>
  )
}

export default function LeftPanel() {
  const {
    sessionId, stage, imageInfo, analysisResult, vectorResult,
    preprocessSettings, vectorizeSettings, numColors,
    setStage, setPreprocessedUrl, setQuantized, setVectorResult, setAnalysisResult,
    updatePreprocessSettings, updateVectorizeSettings, setNumColors,
    setViewMode, setShowExportModal,
  } = useAppStore()

  const [openSections, setOpenSections] = useState<Record<SectionId, boolean>>({
    image: true, preprocess: true, quantize: true, vectorize: true,
  })

  const toggle = (id: SectionId) =>
    setOpenSections(s => ({ ...s, [id]: !s[id] }))

  const isProcessing = ['preprocessing', 'quantizing', 'vectorizing'].includes(stage)
  const hasImage = !!imageInfo && !!sessionId

  // ── Preprocess ─────────────────────────────────────────────────────────
  const handlePreprocess = async () => {
    if (!sessionId) return
    setStage('preprocessing')
    try {
      const result = await preprocessImage({
        session_id: sessionId,
        denoise_enabled: preprocessSettings.denoiseEnabled,
        denoise_strength: preprocessSettings.denoiseStrength,
        sharpen_enabled: preprocessSettings.sharpenEnabled,
        sharpen_strength: preprocessSettings.sharpenStrength,
        contrast: preprocessSettings.contrast,
        brightness: preprocessSettings.brightness,
        saturation: preprocessSettings.saturation,
        bg_removal_enabled: preprocessSettings.bgRemovalEnabled,
        bg_color: preprocessSettings.bgColor,
        bg_tolerance: preprocessSettings.bgTolerance,
        bg_auto_detect: preprocessSettings.bgAutoDetect,
        antialias_cleanup: preprocessSettings.antialiasCleanup,
      })
      setPreprocessedUrl(result.preview_url)
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  // ── Quantize ───────────────────────────────────────────────────────────
  const handleQuantize = async () => {
    if (!sessionId) return
    setStage('quantizing')
    try {
      const result = await quantizeImage({
        session_id: sessionId,
        num_colors: numColors,
        method: 'auto',
        use_preprocessed: true,
      })
      setQuantized(result.palette, result.preview_url)
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  // ── Vectorize ──────────────────────────────────────────────────────────
  const handleVectorize = async () => {
    if (!sessionId) return
    setStage('vectorizing')
    try {
      const result = await vectorizeImage({
        session_id: sessionId,
        image_mode: vectorizeSettings.imageMode,
        quality_preset: vectorizeSettings.qualityPreset,
        color_precision: vectorizeSettings.colorPrecision,
        layer_difference: vectorizeSettings.layerDifference,
        corner_threshold: vectorizeSettings.cornerThreshold,
        length_threshold: vectorizeSettings.lengthThreshold,
        filter_speckle: vectorizeSettings.filterSpeckle,
        curve_fitting: vectorizeSettings.curveFitting,
        min_area: vectorizeSettings.minArea,
        simplify_tolerance: vectorizeSettings.simplifyTolerance,
        group_by_color: vectorizeSettings.groupByColor,
      })
      setVectorResult(result)
      setViewMode('vector')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const handleExportSVG = async () => {
    if (!sessionId || !vectorResult) return
    try {
      const blob = await exportSVG(sessionId, true)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorizer'}_vector.svg`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert('Export failed: ' + (err?.response?.data?.detail || err.message))
    }
  }

  const handleExportPNG = async (scale: 1 | 2 | 4 | 8) => {
    if (!sessionId || !vectorResult) return
    try {
      const blob = await exportPNG(sessionId, scale)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorizer'}_${scale}x.png`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert('PNG export failed: ' + (err?.response?.data?.detail || err.message))
    }
  }

  const COLOR_PRESETS = [2, 4, 6, 8, 12, 16, 24, 32, 48, 64]

  return (
    <div className="left-panel">
      <div className="panel-scroll">

        {/* ── Image Info ─────────────────────────────────────────────────── */}
        {imageInfo && (
          <Section id="image" title="Image Info" open={openSections.image} onToggle={() => toggle('image')}>
            <div className="image-info-card">
              <div className="image-info-row">
                <span className="image-info-label">File</span>
                <span className="image-info-value" style={{maxWidth:150, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>
                  {imageInfo.filename}
                </span>
              </div>
              <div className="image-info-row">
                <span className="image-info-label">Dimensions</span>
                <span className="image-info-value">{imageInfo.width} × {imageInfo.height} px</span>
              </div>
              <div className="image-info-row">
                <span className="image-info-label">Format</span>
                <span className="image-info-value">{imageInfo.format} · {imageInfo.mode}</span>
              </div>
              <div className="image-info-row">
                <span className="image-info-label">Size</span>
                <span className="image-info-value">{(imageInfo.file_size_bytes / 1024).toFixed(1)} KB</span>
              </div>
              <div className="image-info-row">
                <span className="image-info-label">Alpha</span>
                <span className={`image-info-value ${imageInfo.has_alpha ? 'text-success' : ''}`}>
                  {imageInfo.has_alpha ? 'Yes (transparent)' : 'No'}
                </span>
              </div>
            </div>

            {/* Analysis Result */}
            {analysisResult && (
              <div style={{marginTop: 8}}>
                <div className="flex-row" style={{marginBottom: 6}}>
                  <span className="image-info-label">Recommended Mode</span>
                </div>
                <div className="flex-row">
                  <span className={`analysis-mode-badge mode-${analysisResult.recommended_mode}`}>
                    {analysisResult.recommended_mode.toUpperCase()}
                  </span>
                  <span style={{fontSize:11, color:'var(--text-muted)'}}>
                    {Math.round(analysisResult.confidence * 100)}% confidence
                  </span>
                </div>
                <div className="confidence-bar" style={{marginTop:6}}>
                  <div className="confidence-fill" style={{width: `${analysisResult.confidence*100}%`}} />
                </div>
                <div style={{fontSize:11, color:'var(--text-muted)', marginTop:6, lineHeight:1.4}}>
                  {analysisResult.notes}
                </div>
              </div>
            )}
          </Section>
        )}

        {/* ── Preprocessing ─────────────────────────────────────────────── */}
        {hasImage && (
          <Section id="preprocess" title="Preprocessing" open={openSections.preprocess} onToggle={() => toggle('preprocess')}>
            <Toggle label="Noise Reduction" value={preprocessSettings.denoiseEnabled}
              onChange={v => updatePreprocessSettings({ denoiseEnabled: v })} disabled={isProcessing} />
            {preprocessSettings.denoiseEnabled && (
              <Slider label="Strength" value={preprocessSettings.denoiseStrength} min={1} max={20} step={0.5}
                onChange={v => updatePreprocessSettings({ denoiseStrength: v })} disabled={isProcessing} />
            )}

            <div className="h-divider" />

            <Slider label="Contrast" value={preprocessSettings.contrast} min={0.1} max={3.0} step={0.05}
              onChange={v => updatePreprocessSettings({ contrast: v })} disabled={isProcessing} />
            <Slider label="Brightness" value={preprocessSettings.brightness} min={0.1} max={3.0} step={0.05}
              onChange={v => updatePreprocessSettings({ brightness: v })} disabled={isProcessing} />
            <Slider label="Saturation" value={preprocessSettings.saturation} min={0.0} max={3.0} step={0.05}
              onChange={v => updatePreprocessSettings({ saturation: v })} disabled={isProcessing} />

            <div className="h-divider" />

            <Toggle label="Edge Enhancement" value={preprocessSettings.sharpenEnabled}
              onChange={v => updatePreprocessSettings({ sharpenEnabled: v })} disabled={isProcessing} />
            {preprocessSettings.sharpenEnabled && (
              <Slider label="Strength" value={preprocessSettings.sharpenStrength} min={0} max={2.0} step={0.05}
                onChange={v => updatePreprocessSettings({ sharpenStrength: v })} disabled={isProcessing} />
            )}

            <Toggle label="Anti-alias Cleanup" value={preprocessSettings.antialiasCleanup}
              onChange={v => updatePreprocessSettings({ antialiasCleanup: v })} disabled={isProcessing} />

            <div className="h-divider" />

            <Toggle label="Background Removal" value={preprocessSettings.bgRemovalEnabled}
              onChange={v => updatePreprocessSettings({ bgRemovalEnabled: v })} disabled={isProcessing} />
            {preprocessSettings.bgRemovalEnabled && (
              <>
                <Toggle label="Auto-detect Color" value={preprocessSettings.bgAutoDetect}
                  onChange={v => updatePreprocessSettings({ bgAutoDetect: v })} disabled={isProcessing} />
                <Slider label="Tolerance" value={preprocessSettings.bgTolerance} min={0} max={100} step={1}
                  onChange={v => updatePreprocessSettings({ bgTolerance: v })} disabled={isProcessing} />
              </>
            )}

            <button
              className="btn btn-secondary full-width"
              onClick={handlePreprocess}
              disabled={isProcessing}
              style={{marginTop: 4}}
            >
              {stage === 'preprocessing' ? <><span className="spinner" style={{width:12,height:12}} /> Processing…</> : '⚙ Apply Preprocessing'}
            </button>
          </Section>
        )}

        {/* ── Color Quantization ────────────────────────────────────────── */}
        {hasImage && (
          <Section id="quantize" title="Color Quantization" open={openSections.quantize} onToggle={() => toggle('quantize')}>
            <div className="control-label" style={{marginBottom:6}}>
              <span>Colors</span>
              <span className="value-display mono">{numColors}</span>
            </div>
            <div className="color-presets">
              {COLOR_PRESETS.map(n => (
                <button
                  key={n}
                  className={`color-preset-btn ${numColors === n ? 'active' : ''}`}
                  onClick={() => setNumColors(n)}
                  disabled={isProcessing}
                >
                  {n}
                </button>
              ))}
            </div>

            <button
              className="btn btn-secondary full-width"
              onClick={handleQuantize}
              disabled={isProcessing}
              style={{marginTop:8}}
            >
              {stage === 'quantizing' ? <><span className="spinner" style={{width:12,height:12}} /> Quantizing…</> : '🎨 Reduce Colors'}
            </button>
          </Section>
        )}

        {/* ── Vectorization ─────────────────────────────────────────────── */}
        {hasImage && (
          <Section id="vectorize" title="Vectorization" open={openSections.vectorize} onToggle={() => toggle('vectorize')}>
            <div className="control-group">
              <div className="control-label"><span>Image Mode</span></div>
              <select
                value={vectorizeSettings.imageMode}
                onChange={e => updateVectorizeSettings({ imageMode: e.target.value as any })}
                disabled={isProcessing}
              >
                <option value="auto">AUTO (Recommended)</option>
                <option value="logo">Logo / Clipart</option>
                <option value="photo">Photo</option>
                <option value="sketch">Sketch</option>
                <option value="bw">Black & White</option>
              </select>
            </div>

            <div className="control-group">
              <div className="control-label"><span>Quality Preset</span></div>
              <div className="segment-tabs">
                {(['fast','balanced','high','ultra'] as const).map(p => (
                  <button
                    key={p}
                    className={`segment-tab ${vectorizeSettings.qualityPreset === p ? 'active' : ''}`}
                    onClick={() => updateVectorizeSettings({ qualityPreset: p })}
                    disabled={isProcessing}
                  >
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <div className="control-group">
              <div className="control-label"><span>Curve Fitting</span></div>
              <select
                value={vectorizeSettings.curveFitting}
                onChange={e => updateVectorizeSettings({ curveFitting: e.target.value as any })}
                disabled={isProcessing}
              >
                <option value="spline">Spline (smooth curves)</option>
                <option value="polygon">Polygon (sharp corners)</option>
                <option value="pixel">Pixel (exact pixels)</option>
              </select>
            </div>

            <div className="h-divider" />

            <Slider label="Color Precision" value={vectorizeSettings.colorPrecision} min={1} max={8} step={1}
              onChange={v => updateVectorizeSettings({ colorPrecision: v })} disabled={isProcessing} />
            <Slider label="Layer Difference" value={vectorizeSettings.layerDifference} min={1} max={64} step={1}
              onChange={v => updateVectorizeSettings({ layerDifference: v })} disabled={isProcessing} />
            <Slider label="Corner Threshold" value={vectorizeSettings.cornerThreshold} min={0} max={180} step={1}
              onChange={v => updateVectorizeSettings({ cornerThreshold: v })} disabled={isProcessing} />
            <Slider label="Path Smoothing" value={vectorizeSettings.lengthThreshold} min={0.5} max={20} step={0.5}
              onChange={v => updateVectorizeSettings({ lengthThreshold: v })} disabled={isProcessing} />
            <Slider label="Speckle Filter" value={vectorizeSettings.filterSpeckle} min={0} max={64} step={1}
              onChange={v => updateVectorizeSettings({ filterSpeckle: v })} disabled={isProcessing} />
            <Slider label="Min Path Area" value={vectorizeSettings.minArea} min={0} max={100} step={1}
              onChange={v => updateVectorizeSettings({ minArea: v })} disabled={isProcessing} />

            <Toggle label="Group by Color" value={vectorizeSettings.groupByColor}
              onChange={v => updateVectorizeSettings({ groupByColor: v })} disabled={isProcessing} />

            <button
              className="btn btn-primary full-width"
              onClick={handleVectorize}
              disabled={isProcessing}
              style={{marginTop:8}}
            >
              {stage === 'vectorizing'
                ? <><span className="spinner" style={{width:14,height:14}} /> Vectorizing…</>
                : '◈ Vectorize'}
            </button>

            {vectorResult && (
              <div className="export-ready-card" style={{ marginTop: 14, padding: '12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--accent-primary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ color: 'var(--success)', fontWeight: 600, fontSize: 12 }}>✓ Vector Ready</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>{vectorResult.stats.path_count} paths</span>
                </div>
                <button
                  className="btn btn-primary full-width"
                  style={{ marginBottom: 8, fontWeight: 600 }}
                  onClick={() => setShowExportModal(true)}
                >
                  ⤓ Export / Download As…
                </button>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={handleExportSVG}
                    title="Download SVG"
                  >
                    ⬇ SVG
                  </button>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleExportPNG(2)}
                    title="Download 2× HD PNG"
                  >
                    ⬇ 2× PNG
                  </button>
                </div>
              </div>
            )}
          </Section>
        )}

        {/* Error display */}
        {stage === 'error' && (
          <div className="alert alert-error" style={{marginTop: 8}}>
            ⚠ {useAppStore.getState().errorMessage}
          </div>
        )}
      </div>
    </div>
  )
}

