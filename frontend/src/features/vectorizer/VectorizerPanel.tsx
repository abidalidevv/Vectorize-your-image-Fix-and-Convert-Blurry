import React, { useState } from 'react'
import { useAppStore } from '../../store/appStore'
import {
  preprocessImage,
  quantizeImage,
  vectorizeImage,
  exportSVG,
  exportPNG,
} from '../../api/client'

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

type SectionId = 'preprocess' | 'quantize' | 'vectorize'

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

export default function VectorizerPanel() {
  const {
    sessionId, stage, imageInfo, analysisResult, vectorResult,
    preprocessSettings, vectorizeSettings, numColors,
    vectorizeSourceStage, setVectorizeSourceStage,
    setStage, setPreprocessedUrl, setQuantized, setVectorResult,
    updatePreprocessSettings, updateVectorizeSettings,
    setNumColors, setViewMode, setShowExportModal,
  } = useAppStore()

  const [openSections, setOpenSections] = useState<Record<SectionId, boolean>>({
    preprocess: true,
    quantize: true,
    vectorize: true,
  })

  const toggle = (id: SectionId) =>
    setOpenSections(s => ({ ...s, [id]: !s[id] }))

  const isProcessing = ['preprocessing', 'quantizing', 'vectorizing'].includes(stage)

  const [appliedRecommended, setAppliedRecommended] = useState<string | null>(null)

  const handleApplyRecommended = () => {
    if (!analysisResult) return
    const mode = analysisResult.recommended_mode
    if (mode === 'logo') {
      updateVectorizeSettings({
        imageMode: 'logo',
        qualityPreset: 'high',
        filterSpeckle: 0,
        colorPrecision: 8,
        layerDifference: 12,
        cornerThreshold: 60,
        curveFitting: 'spline',
      })
      setAppliedRecommended('Logo settings applied: Speckle=0 (Preserves fine outlines & borders), Spline curves')
    } else if (mode === 'bw') {
      updateVectorizeSettings({
        imageMode: 'bw',
        qualityPreset: 'high',
        filterSpeckle: 0,
        curveFitting: 'spline',
      })
      setAppliedRecommended('B&W settings applied: True geometric circle/line primitives active')
    } else if (mode === 'sketch') {
      updateVectorizeSettings({
        imageMode: 'sketch',
        qualityPreset: 'high',
        filterSpeckle: 1,
        curveFitting: 'spline',
      })
      updatePreprocessSettings({
        denoiseEnabled: true,
        denoiseStrength: 2.5,
        contrast: 1.3,
      })
      setAppliedRecommended('Sketch settings applied: CLAHE contrast boost & line smoothing')
    } else if (mode === 'photo') {
      updateVectorizeSettings({
        imageMode: 'photo',
        qualityPreset: 'high',
        filterSpeckle: 2,
        colorPrecision: 8,
        layerDifference: 8,
        curveFitting: 'spline',
      })
      setAppliedRecommended('Photo settings applied: Continuous tone palette & high precision')
    } else {
      updateVectorizeSettings({
        imageMode: 'auto',
        qualityPreset: 'high',
        filterSpeckle: 0,
        curveFitting: 'spline',
      })
      setAppliedRecommended('Recommended Auto settings applied')
    }
    setTimeout(() => setAppliedRecommended(null), 4500)
  }

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

  const handleQuantize = async () => {
    if (!sessionId) return
    setStage('quantizing')
    try {
      const result = await quantizeImage({
        session_id: sessionId,
        num_colors: numColors,
        method: 'auto',
        use_preprocessed: !!useAppStore.getState().preprocessedUrl,
      })
      setQuantized(result.palette, result.preview_url)
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

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
        source_stage: vectorizeSourceStage,
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
    <>
      {/* Recommended Settings Card */}
      {analysisResult && (
        <div style={{
          marginBottom: 'var(--space-3)',
          padding: '12px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          width: '100%',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}>
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

          <button
            type="button"
            className="btn btn-primary full-width"
            onClick={handleApplyRecommended}
            disabled={isProcessing}
            style={{
              marginTop: 10,
              width: '100%',
              maxWidth: '100%',
              boxSizing: 'border-box',
              whiteSpace: 'normal',
              textAlign: 'center',
              lineHeight: 1.35,
              background: 'linear-gradient(135deg, #5b6ef7 0%, #8b5cf6 100%)',
              boxShadow: '0 2px 10px rgba(91, 110, 247, 0.3)',
              fontWeight: 600,
              fontSize: 12,
              padding: '8px 10px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              cursor: 'pointer'
            }}
            title={`Automatically apply the best settings tailored for ${analysisResult.recommended_mode.toUpperCase()} images`}
          >
            <span>Recommended Settings</span>
          </button>

          {appliedRecommended && (
            <div style={{
              marginTop: 6,
              padding: '6px 10px',
              borderRadius: 6,
              background: 'rgba(52, 211, 153, 0.15)',
              border: '1px solid rgba(52, 211, 153, 0.4)',
              color: '#34d399',
              fontSize: 11,
              fontWeight: 500,
              lineHeight: 1.3
            }}>
              ✓ {appliedRecommended}
            </div>
          )}

          <div style={{marginTop: 8, textAlign: 'center'}}>
            <a
              href="/documentation.html#image-guide"
              target="_blank"
              rel="noopener"
              style={{
                fontSize: 11,
                color: 'var(--accent-primary)',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 4
              }}
            >
              📖 Read Image Settings Guide ↗
            </a>
          </div>
        </div>
      )}

      {/* ── Preprocess ─────────────────────────────────────────────── */}
      <Section id="preprocess" title="Preprocessing" open={openSections.preprocess} onToggle={() => toggle('preprocess')}>
        <Toggle label="Noise Reduction" value={preprocessSettings.denoiseEnabled}
          onChange={v => updatePreprocessSettings({ denoiseEnabled: v })} disabled={isProcessing} />
        {preprocessSettings.denoiseEnabled && (
          <Slider label="Noise Strength" value={preprocessSettings.denoiseStrength} min={1} max={20} step={0.5}
            onChange={v => updatePreprocessSettings({ denoiseStrength: v })} disabled={isProcessing} />
        )}

        <Toggle label="Sharpen Edges" value={preprocessSettings.sharpenEnabled}
          onChange={v => updatePreprocessSettings({ sharpenEnabled: v })} disabled={isProcessing} />
        {preprocessSettings.sharpenEnabled && (
          <Slider label="Sharpen Strength" value={preprocessSettings.sharpenStrength} min={0.1} max={2} step={0.1}
            onChange={v => updatePreprocessSettings({ sharpenStrength: v })} disabled={isProcessing} />
        )}

        <Slider label="Contrast" value={preprocessSettings.contrast} min={0.5} max={2.0} step={0.05}
          onChange={v => updatePreprocessSettings({ contrast: v })} disabled={isProcessing} />
        <Slider label="Brightness" value={preprocessSettings.brightness} min={0.5} max={2.0} step={0.05}
          onChange={v => updatePreprocessSettings({ brightness: v })} disabled={isProcessing} />
        <Slider label="Saturation" value={preprocessSettings.saturation} min={0.0} max={2.0} step={0.05}
          onChange={v => updatePreprocessSettings({ saturation: v })} disabled={isProcessing} />

        <Toggle label="Anti-Alias Cleanup" value={preprocessSettings.antialiasCleanup}
          onChange={v => updatePreprocessSettings({ antialiasCleanup: v })} disabled={isProcessing} />

        <button
          className="btn btn-secondary full-width"
          onClick={handlePreprocess}
          disabled={isProcessing}
          style={{marginTop:8}}
        >
          {stage === 'preprocessing' ? <><span className="spinner" style={{width:12,height:12}} /> Processing…</> : 'Apply Preprocessing'}
        </button>
      </Section>

      {/* ── Color Quantization ─────────────────────────────────────── */}
      <Section id="quantize" title="Color Quantization" open={openSections.quantize} onToggle={() => toggle('quantize')}>
        <div className="control-group">
          <div className="control-label">
            <span>Target Colors</span>
            <span className="value-display">{numColors}</span>
          </div>
          <div className="segment-tabs" style={{flexWrap:'wrap', gap:3}}>
            {COLOR_PRESETS.map(n => (
              <button
                key={n}
                className={`segment-tab ${numColors === n ? 'active' : ''}`}
                onClick={() => setNumColors(n)}
                disabled={isProcessing}
                style={{minWidth:28, flex:'0 0 auto'}}
              >
                {n}
              </button>
            ))}
          </div>
        </div>

        <Slider
          label="Custom Color Count"
          value={numColors}
          min={2}
          max={64}
          step={1}
          onChange={v => setNumColors(Math.round(v))}
          disabled={isProcessing}
        />

        <button
          className="btn btn-secondary full-width"
          onClick={handleQuantize}
          disabled={isProcessing}
          style={{marginTop:8}}
        >
          {stage === 'quantizing' ? <><span className="spinner" style={{width:12,height:12}} /> Quantizing…</> : 'Quantize Colors'}
        </button>

        <div className="control-group" style={{marginTop: 10}}>
          <div className="control-label">
            <span>Vectorize Source</span>
            <span className="value-display" style={{textTransform: 'capitalize'}}>{vectorizeSourceStage}</span>
          </div>
          <div className="segment-tabs">
            <button
              type="button"
              className={`segment-tab ${vectorizeSourceStage === 'auto' ? 'active' : ''}`}
              onClick={() => setVectorizeSourceStage('auto')}
              disabled={isProcessing}
              title="Auto: uses quantized for logos if available, otherwise original/preprocessed"
            >
              Auto
            </button>
            <button
              type="button"
              className={`segment-tab ${vectorizeSourceStage === 'original' ? 'active' : ''}`}
              onClick={() => setVectorizeSourceStage('original')}
              disabled={isProcessing}
              title="Force using original image for vectorization"
            >
              Use Original
            </button>
            <button
              type="button"
              className={`segment-tab ${vectorizeSourceStage === 'quantized' ? 'active' : ''}`}
              onClick={() => setVectorizeSourceStage('quantized')}
              disabled={isProcessing}
              title="Force using quantized image for vectorization"
            >
              Use Quantized
            </button>
          </div>
        </div>
      </Section>

      {/* ── Vectorization ─────────────────────────────────────────── */}
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
    </>
  )
}
