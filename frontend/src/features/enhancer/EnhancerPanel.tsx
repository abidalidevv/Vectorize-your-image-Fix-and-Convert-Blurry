import React, { useState } from 'react'
import { useAppStore } from '../../store/appStore'
import { enhanceImage } from '../../api/client'

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

export default function EnhancerPanel() {
  const {
    sessionId, stage, imageInfo, analysisResult,
    enhancerSettings, updateEnhancerSettings,
    enhancedResult, setEnhancedResult,
    setStage, setViewMode, setActiveTool, setVectorizeSourceStage,
  } = useAppStore()

  const [appliedRecommended, setAppliedRecommended] = useState<string | null>(null)

  const isProcessing = stage === 'enhancing'

  const handleApplyRecommended = () => {
    if (!analysisResult) return
    const mode = analysisResult.recommended_mode
    if (mode === 'logo' || mode === 'sketch' || mode === 'bw') {
      updateEnhancerSettings({
        quality: 'fast',
        modelTier: 'default',
        scale: 2,
        sharpenStrength: 1.2,
        denoiseStrength: 0.0,
        claheEnabled: true,
        clarity: 0.4,
        contrast: 1.05,
        brightness: 1.0,
        saturation: 1.0,
      })
      setAppliedRecommended('Logo/Graphic settings applied: 2× Clean Super-Resolution & Sharp Outlines')
    } else if (mode === 'photo') {
      updateEnhancerSettings({
        quality: 'ultra',
        modelTier: 'pro',
        scale: 2,
        sharpenStrength: 0.8,
        denoiseStrength: 1.5,
        claheEnabled: true,
        clarity: 0.35,
        contrast: 1.05,
        brightness: 1.02,
        saturation: 1.1,
      })
      setAppliedRecommended('Photo settings applied: Pro Deep AI Super-Resolution (2×) & Tone Restoration')
    } else {
      updateEnhancerSettings({
        quality: 'fast',
        modelTier: 'default',
        scale: 2,
        sharpenStrength: 1.0,
        denoiseStrength: 0.8,
        claheEnabled: true,
        clarity: 0.3,
        contrast: 1.0,
        brightness: 1.0,
        saturation: 1.0,
      })
      setAppliedRecommended('Balanced settings applied: 2× AI Super-Resolution + Clarity')
    }
    setTimeout(() => setAppliedRecommended(null), 4500)
  }

  const handleEnhance = async () => {
    if (!sessionId) return
    setStage('enhancing')
    try {
      const res = await enhanceImage({
        session_id: sessionId,
        quality: enhancerSettings.quality,
        model_tier: enhancerSettings.modelTier,
        scale: enhancerSettings.scale,
        sharpen_strength: enhancerSettings.sharpenStrength,
        denoise_strength: enhancerSettings.denoiseStrength,
        clahe_enabled: enhancerSettings.claheEnabled,
        contrast: enhancerSettings.contrast,
        brightness: enhancerSettings.brightness,
        saturation: enhancerSettings.saturation,
        clarity: enhancerSettings.clarity,
        face_restore: enhancerSettings.faceRestore,
        face_fidelity: enhancerSettings.faceFidelity,
      })
      setEnhancedResult({
        url: res.preview_url,
        width: res.width,
        height: res.height,
        changesApplied: res.changes_applied,
      })
      // Immediately switch view to enhanced so user sees results
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const isUltra = enhancerSettings.quality === 'ultra' || enhancerSettings.modelTier === 'pro'

  return (
    <div className="panel-section-content">
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
          <div className="flex-row" style={{ marginBottom: 6 }}>
            <span className="image-info-label" style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
              AI Image Detection
            </span>
          </div>
          <div className="flex-row" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`analysis-mode-badge mode-${analysisResult.recommended_mode}`}>
              {analysisResult.recommended_mode.toUpperCase()}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {Math.round(analysisResult.confidence * 100)}% confidence
            </span>
          </div>
          <div className="confidence-bar" style={{ marginTop: 6 }}>
            <div className="confidence-fill" style={{ width: `${analysisResult.confidence * 100}%` }} />
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
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
            title={`Apply optimal enhancement settings tailored for ${analysisResult.recommended_mode.toUpperCase()} images`}
          >
            <span>Recommended Settings</span>
          </button>

          {appliedRecommended && (
            <div style={{
              marginTop: 8,
              padding: '6px 10px',
              background: 'rgba(52, 211, 153, 0.12)',
              border: '1px solid rgba(52, 211, 153, 0.35)',
              borderRadius: 'var(--radius-sm)',
              fontSize: 11,
              color: 'var(--success)',
              lineHeight: 1.35,
            }}>
              ✓ {appliedRecommended}
            </div>
          )}
        </div>
      )}

      {/* Model Tier Selector: Standard vs Pro */}
      <div className="control-group" style={{ marginBottom: 12 }}>
        <div className="control-label" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Model Tier</span>
          <span style={{
            fontSize: 10.5,
            fontWeight: 600,
            color: isUltra ? '#f472b6' : '#10b981',
            background: isUltra ? 'rgba(236, 72, 153, 0.12)' : 'rgba(16, 185, 129, 0.12)',
            border: isUltra ? '1px solid rgba(244, 114, 182, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)',
            padding: '2px 7px',
            borderRadius: 'var(--radius-sm)',
          }}>
            Model : {isUltra ? 'RealESRGAN x4+' : 'Real-ESRGAN v3'}
          </span>
        </div>
        <div className="segment-tabs" style={{ marginTop: 6 }}>
          <button
            type="button"
            className={`segment-tab ${!isUltra ? 'active' : ''}`}
            onClick={() => updateEnhancerSettings({
              quality: 'fast',
              modelTier: 'default',
              scale: enhancerSettings.scale === 1 ? 2 : enhancerSettings.scale
            })}
            disabled={isProcessing}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              fontWeight: 600,
              background: !isUltra ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : undefined,
              color: !isUltra ? '#ffffff' : undefined,
              boxShadow: !isUltra ? '0 2px 10px rgba(16, 185, 129, 0.4)' : undefined,
              border: !isUltra ? 'none' : undefined,
              transition: 'all 0.2s ease',
            }}
          >
            Standard
          </button>
          <button
            type="button"
            className={`segment-tab ${isUltra ? 'active' : ''}`}
            onClick={() => updateEnhancerSettings({
              quality: 'ultra',
              modelTier: 'pro',
              scale: enhancerSettings.scale === 1 ? 4 : enhancerSettings.scale
            })}
            disabled={isProcessing}
            style={{
              padding: '6px 12px',
              fontSize: 12,
              fontWeight: 600,
              background: isUltra ? 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)' : undefined,
              color: isUltra ? '#ffffff' : undefined,
              boxShadow: isUltra ? '0 2px 10px rgba(236, 72, 153, 0.4)' : undefined,
              border: isUltra ? 'none' : undefined,
              transition: 'all 0.2s ease',
            }}
          >
            Pro
          </button>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
          {isUltra
            ? '👑 Pro Mode: Deep RRDBNet neural reconstruction. Maximum detail & photorealistic clarity (~4–8s).'
            : '⚡ Standard Mode: Ultra-fast (~1–2s) lightweight Real-ESRGAN v3 upscaling + tone clarity.'}
        </div>
      </div>

      {/* Presets */}
      <div className="control-group">
        <div className="control-label"><span>Enhancement Presets</span></div>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:6, marginTop:4}}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateEnhancerSettings({
              scale: 2, sharpenStrength: 0.8, denoiseStrength: 1.0, claheEnabled: true, clarity: 0.3, contrast: 1.0, brightness: 1.0, saturation: 1.0
            })}
            title="Balanced Auto Enhancement"
          >
            ⚡ Auto Enhance
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateEnhancerSettings({
              scale: 2, sharpenStrength: 1.0, denoiseStrength: 0.0, claheEnabled: true, clarity: 0.4, contrast: 1.05, brightness: 1.0, saturation: 1.0
            })}
            title="2x Super Resolution + Clarity"
          >
            🔍 2× Super-Res
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateEnhancerSettings({
              scale: 4, sharpenStrength: 1.2, denoiseStrength: 0.0, claheEnabled: true, clarity: 0.5, contrast: 1.05, brightness: 1.0, saturation: 1.0
            })}
            title="4x Ultra Magnification"
          >
            🚀 4× Ultra-Res
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateEnhancerSettings({
              scale: 2, sharpenStrength: 1.0, denoiseStrength: 3.5, claheEnabled: true, clarity: 0.4, contrast: 1.1, brightness: 1.02, saturation: 1.15, faceRestore: true, faceFidelity: 0.85
            })}
            title="Photo Restoration & Tone (Includes Face Restoration AI)"
          >
            ✨ Photo Restore
          </button>
        </div>
      </div>

      {/* Upscaling */}
      <div className="control-group" style={{marginTop:12}}>
        <div className="control-label"><span>Upscaling Factor</span></div>
        <div className="segment-tabs">
          {([1, 2, 4] as const).map(s => (
            <button
              key={s}
              type="button"
              className={`segment-tab ${enhancerSettings.scale === s ? 'active' : ''}`}
              onClick={() => updateEnhancerSettings({ scale: s })}
              disabled={isProcessing}
            >
              {s === 1 ? '1× (Original)' : `${s}× HD`}
            </button>
          ))}
        </div>
      </div>

      <div className="h-divider" />

      <Slider
        label="Sharpen & Deblur"
        value={enhancerSettings.sharpenStrength}
        min={0} max={2.5} step={0.1}
        onChange={v => updateEnhancerSettings({ sharpenStrength: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Denoise / JPEG Cleanup"
        value={enhancerSettings.denoiseStrength}
        min={0} max={10} step={0.5}
        onChange={v => updateEnhancerSettings({ denoiseStrength: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Clarity & Mid-tone Contrast"
        value={enhancerSettings.clarity}
        min={0} max={1.0} step={0.05}
        onChange={v => updateEnhancerSettings({ clarity: v })}
        disabled={isProcessing}
      />

      <Toggle
        label="CLAHE Dynamic Tone Equalization"
        value={enhancerSettings.claheEnabled}
        onChange={v => updateEnhancerSettings({ claheEnabled: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Contrast"
        value={enhancerSettings.contrast}
        min={0.5} max={1.8} step={0.05}
        onChange={v => updateEnhancerSettings({ contrast: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Brightness"
        value={enhancerSettings.brightness}
        min={0.5} max={1.8} step={0.05}
        onChange={v => updateEnhancerSettings({ brightness: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Saturation / Vibrance"
        value={enhancerSettings.saturation}
        min={0.0} max={2.0} step={0.05}
        onChange={v => updateEnhancerSettings({ saturation: v })}
        disabled={isProcessing}
      />

      <div className="h-divider" />

      {/* Face Restoration (GFPGAN AI) */}
      <div style={{
        padding: '10px 12px',
        background: enhancerSettings.faceRestore ? 'rgba(168, 85, 247, 0.12)' : 'var(--bg-elevated)',
        border: enhancerSettings.faceRestore ? '1.5px solid rgba(168, 85, 247, 0.45)' : '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        transition: 'all 0.2s ease',
        marginBottom: 10,
      }}>
        <Toggle
          label="👤 Face Restoration (GFPGAN AI)"
          value={enhancerSettings.faceRestore}
          onChange={v => updateEnhancerSettings({ faceRestore: v })}
          disabled={isProcessing}
        />
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, lineHeight: 1.4 }}>
          {enhancerSettings.faceRestore
            ? 'Detects and restores blurred/scratched faces with realistic eyes, skin, and facial geometry.'
            : 'Toggle on to detect and restore facial details in portraits and old vintage photos.'}
        </div>
        {enhancerSettings.faceRestore && (
          <div style={{ marginTop: 10 }}>
            <Slider
              label="Face Detail Blend (Fidelity)"
              value={enhancerSettings.faceFidelity}
              min={0.1} max={1.0} step={0.05}
              onChange={v => updateEnhancerSettings({ faceFidelity: v })}
              disabled={isProcessing}
            />
          </div>
        )}
      </div>

      {enhancedResult && (
        <div style={{
          marginTop: 14,
          padding: '12px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--success)',
          width: '100%',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6}}>
            <span style={{color:'var(--success)', fontWeight:600, fontSize:12}}>✓ Enhanced Image Ready</span>
            <span style={{fontSize:11, color:'var(--text-muted)'}}>{enhancedResult.width} × {enhancedResult.height} px</span>
          </div>
          <div style={{display:'flex', flexWrap:'wrap', gap:4, marginBottom:10}}>
            {enhancedResult.changesApplied.map((c, i) => (
              <span key={i} style={{fontSize:10, padding:'2px 6px', borderRadius:4, background:'rgba(16,185,129,0.15)', color:'#10b981'}}>
                {c}
              </span>
            ))}
          </div>
          <div style={{display:'flex', flexDirection:'column', gap:6, width:'100%', boxSizing:'border-box'}}>
            <button
              type="button"
              className="btn btn-primary full-width btn-sm"
              style={{
                width: '100%',
                maxWidth: '100%',
                boxSizing: 'border-box',
                whiteSpace: 'normal',
                textAlign: 'center',
                padding: '8px 10px',
                lineHeight: 1.3,
                fontSize: 12,
                cursor: 'pointer'
              }}
              onClick={() => {
                const a = document.createElement('a')
                a.href = enhancedResult.url
                a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_enhanced.png`
                a.click()
              }}
            >
              ⬇ Download Enhanced PNG
            </button>
            <button
              type="button"
              className="btn btn-secondary full-width btn-sm"
              style={{
                width: '100%',
                maxWidth: '100%',
                boxSizing: 'border-box',
                whiteSpace: 'normal',
                textAlign: 'center',
                padding: '8px 10px',
                lineHeight: 1.3,
                fontSize: 12,
                cursor: 'pointer'
              }}
              onClick={() => {
                setVectorizeSourceStage('auto')
                setActiveTool('vectorizer')
              }}
            >
              ⚡ Jump to Vectorizer →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
