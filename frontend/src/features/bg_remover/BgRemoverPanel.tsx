import React, { useState } from 'react'
import { useAppStore } from '../../store/appStore'
import { removeBackground } from '../../api/client'

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

function Toggle({ label, value, onChange, disabled = false, note }: {
  label: string; value: boolean; onChange: (v: boolean) => void; disabled?: boolean; note?: string
}) {
  return (
    <div className="control-group" style={{ marginTop: 4 }}>
      <div className="toggle-row">
        <span className="toggle-label">{label}</span>
        <label className="toggle">
          <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />
          <div className="toggle-track">
            <div className="toggle-thumb" />
          </div>
        </label>
      </div>
      {note && <span style={{ fontSize: 10.5, color: 'var(--text-muted)', lineHeight: 1.3 }}>{note}</span>}
    </div>
  )
}

const SWATCHES = [
  { label: 'Transparent', color: 'transparent', type: 'transparent' as const },
  { label: 'White', color: '#ffffff', type: 'color' as const },
  { label: 'Slate', color: '#0f172a', type: 'color' as const },
  { label: 'Studio Gray', color: '#374151', type: 'color' as const },
  { label: 'Royal Blue', color: '#1e40af', type: 'color' as const },
  { label: 'Emerald', color: '#065f46', type: 'color' as const },
  { label: 'Crimson', color: '#e11d48', type: 'color' as const },
  { label: 'Sunset Grad', color: '#f97316', type: 'gradient' as const },
]

export default function BgRemoverPanel() {
  const {
    sessionId, stage, imageInfo, analysisResult,
    bgRemoverSettings, updateBgRemoverSettings,
    bgRemovedResult, setBgRemovedResult,
    setStage, setViewMode, setActiveTool, setVectorizeSourceStage,
  } = useAppStore()

  const [appliedRecommended, setAppliedRecommended] = useState<string | null>(null)

  const isProcessing = stage === 'removing_bg'

  const handleApplyRecommended = () => {
    if (!analysisResult) return
    const mode = analysisResult.recommended_mode
    if (mode === 'logo' || mode === 'sketch' || mode === 'bw') {
      updateBgRemoverSettings({
        quality: 'fast',
        modelTier: 'default',
        engine: 'auto',
        tolerance: 30,
        defringeChoke: 2,
        featherRadius: 0.5,
        contiguous: false,
      })
      setAppliedRecommended('Logo/Graphic settings applied: Fast Cutout with Choke=2 (Zero background halo bleeding)')
    } else if (mode === 'photo') {
      updateBgRemoverSettings({
        quality: 'ultra',
        modelTier: 'pro',
        engine: 'ai',
        tolerance: 35,
        defringeChoke: 1,
        featherRadius: 1.5,
        contiguous: false,
      })
      setAppliedRecommended('Photo settings applied: Pro Boundary Matting with soft feathering for natural hair/edges')
    } else {
      updateBgRemoverSettings({
        quality: 'fast',
        modelTier: 'default',
        engine: 'auto',
        tolerance: 35,
        defringeChoke: 1,
        featherRadius: 1.0,
        contiguous: false,
      })
      setAppliedRecommended('Balanced settings applied: Automatic AI Cutout + Defringe')
    }
    setTimeout(() => setAppliedRecommended(null), 4500)
  }

  const handleRemoveBg = async () => {
    if (!sessionId) return
    setStage('removing_bg')
    try {
      const res = await removeBackground({
        session_id: sessionId,
        quality: bgRemoverSettings.quality,
        model_tier: bgRemoverSettings.modelTier,
        engine: bgRemoverSettings.engine,
        tolerance: bgRemoverSettings.tolerance,
        feather_radius: bgRemoverSettings.featherRadius,
        defringe_choke: bgRemoverSettings.defringeChoke,
        contiguous: bgRemoverSettings.contiguous ?? false,
        bg_type: bgRemoverSettings.bgType,
        bg_color: bgRemoverSettings.bgColor,
      })
      setBgRemovedResult({
        url: res.preview_url,
        width: res.width,
        height: res.height,
        changesApplied: res.changes_applied,
      })
      // Immediately switch view to enhanced so user sees the cutout results
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const isUltra = bgRemoverSettings.quality === 'ultra' || bgRemoverSettings.modelTier === 'pro'

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
          <div className="flex-row" style={{ marginBottom: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="image-info-label" style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
              AI Image Detection
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              {Math.round(analysisResult.confidence * 100)}% confidence
            </span>
          </div>
          <div className="flex-row" style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
            <span className={`analysis-mode-badge mode-${analysisResult.recommended_mode}`}>
              {analysisResult.recommended_mode.toUpperCase()}
            </span>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {analysisResult.recommended_mode === 'photo' ? 'Continuous Tone Photo' : 'Graphic / Vector / Artwork'}
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
            title={`Apply optimal background removal settings tailored for ${analysisResult.recommended_mode.toUpperCase()} images`}
          >
            <span>✨</span>
            <span>Use Recommended Settings ({analysisResult.recommended_mode.toUpperCase()})</span>
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
            fontSize: 10,
            padding: '2px 8px',
            borderRadius: 10,
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            background: isUltra
              ? 'linear-gradient(135deg, rgba(236, 72, 153, 0.25), rgba(168, 85, 247, 0.25))'
              : 'rgba(59, 130, 246, 0.15)',
            color: isUltra ? '#f472b6' : '#60a5fa',
            border: isUltra
              ? '1px solid rgba(244, 114, 182, 0.45)'
              : '1px solid rgba(96, 165, 250, 0.35)',
          }}>
            {isUltra ? '👑 Pro Active' : '⚡ Standard Active'}
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 6 }}>
          <button
            type="button"
            className={`tier-btn ${!isUltra ? 'active-default' : ''}`}
            onClick={() => updateBgRemoverSettings({ quality: 'fast', modelTier: 'default' })}
            disabled={isProcessing}
            style={{
              padding: '10px 8px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              borderRadius: 8,
              border: !isUltra ? '1.5px solid #5b6ef7' : '1px solid var(--border-default)',
              background: !isUltra ? 'rgba(91, 110, 247, 0.14)' : 'var(--bg-elevated)',
              boxShadow: !isUltra ? '0 0 14px rgba(91, 110, 247, 0.25)' : 'none',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
            }}
            title="Fast general-purpose segmentation (ISNet General-Use)"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
              <span style={{ fontSize: 14 }}>⚡</span>
              <span style={{ fontWeight: 700, fontSize: 13, color: !isUltra ? '#ffffff' : 'var(--text-secondary)' }}>Standard</span>
              <span style={{
                fontSize: 9,
                padding: '1px 5px',
                borderRadius: 4,
                background: 'rgba(52, 211, 153, 0.2)',
                color: '#34d399',
                fontWeight: 700
              }}>FREE</span>
            </div>
            <span style={{ fontSize: 10.5, color: !isUltra ? '#93c5fd' : 'var(--text-muted)' }}>
              ISNet General
            </span>
          </button>

          <button
            type="button"
            className={`tier-btn ${isUltra ? 'active-pro' : ''}`}
            onClick={() => updateBgRemoverSettings({ quality: 'ultra', modelTier: 'pro' })}
            disabled={isProcessing}
            style={{
              padding: '10px 8px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 3,
              borderRadius: 8,
              border: isUltra ? '1.5px solid #ec4899' : '1px solid var(--border-default)',
              background: isUltra ? 'linear-gradient(135deg, rgba(168, 85, 247, 0.22) 0%, rgba(236, 72, 153, 0.22) 100%)' : 'var(--bg-elevated)',
              boxShadow: isUltra ? '0 0 16px rgba(236, 72, 153, 0.3)' : 'none',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s ease',
            }}
            title="Pro BiRefNet boundary matting for fine hair and intricate edges"
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}>
              <span style={{ fontSize: 14 }}>👑</span>
              <span style={{ fontWeight: 700, fontSize: 13, color: isUltra ? '#ffffff' : 'var(--text-secondary)' }}>Pro</span>
              <span style={{
                fontSize: 9,
                padding: '1px 5px',
                borderRadius: 4,
                background: 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
                color: '#ffffff',
                fontWeight: 700
              }}>AI PRO</span>
            </div>
            <span style={{ fontSize: 10.5, color: isUltra ? '#f472b6' : 'var(--text-muted)' }}>
              BiRefNet Matting
            </span>
          </button>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
          {isUltra
            ? '👑 Pro Mode: BiRefNet boundary matting for fine hair, fur, and intricate edges.'
            : '⚡ Standard Mode: Ultra-fast (~1–2s) ISNet cutout with color decontamination and edge defringing.'}
        </div>
      </div>

      {/* Presets */}
      <div className="control-group">
        <div className="control-label"><span>Cutout Presets</span></div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 4 }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateBgRemoverSettings({
              tolerance: 35, contiguous: false, defringeChoke: 0, featherRadius: 0.5
            })}
            title="Transparent cutout for line art and drawings"
          >
            🎯 Clipart / Line Art
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => updateBgRemoverSettings({
              tolerance: 30, contiguous: false, defringeChoke: 1, featherRadius: 1.0
            })}
            title="Clean transparent cutout for logos"
          >
            ✨ Flat Logo
          </button>
        </div>
      </div>

      {/* Engine Selection */}
      <div className="control-group" style={{ marginTop: 10 }}>
        <div className="control-label"><span>Segmentation Model</span></div>
        <div className="segment-tabs">
          <button
            type="button"
            className={`segment-tab ${bgRemoverSettings.engine === 'auto' ? 'active' : ''}`}
            onClick={() => updateBgRemoverSettings({ engine: 'auto' })}
            disabled={isProcessing}
            title="Instant Local Cutout with AI fallback"
          >
            Instant Cutout
          </button>
          <button
            type="button"
            className={`segment-tab ${bgRemoverSettings.engine === 'color' ? 'active' : ''}`}
            onClick={() => updateBgRemoverSettings({ engine: 'color' })}
            disabled={isProcessing}
            title="Color & Border Segmentation"
          >
            Color Cutout
          </button>
        </div>
      </div>

      {/* Color Tolerance Slider */}
      <Slider
        label="Color Tolerance"
        value={bgRemoverSettings.tolerance}
        min={5} max={90} step={1}
        onChange={v => updateBgRemoverSettings({ tolerance: v })}
        disabled={isProcessing}
      />

      {/* Contiguous Toggle */}
      <Toggle
        label="Border-Connected Only"
        value={bgRemoverSettings.contiguous ?? false}
        onChange={v => updateBgRemoverSettings({ contiguous: v })}
        disabled={isProcessing}
        note="Off: removes background everywhere (recommended for drawings & logos). On: only removes outer border background."
      />

      <div className="h-divider" />

      {/* Edge Refinement */}
      <Slider
        label="Defringe / Halo Choke"
        value={bgRemoverSettings.defringeChoke}
        min={0} max={4} step={1}
        onChange={v => updateBgRemoverSettings({ defringeChoke: v })}
        disabled={isProcessing}
      />

      <Slider
        label="Edge Feathering Softness"
        value={bgRemoverSettings.featherRadius}
        min={0} max={4} step={0.5}
        onChange={v => updateBgRemoverSettings({ featherRadius: v })}
        disabled={isProcessing}
      />

      <div className="h-divider" />

      {/* Replacement Backdrop */}
      <div className="control-group">
        <div className="control-label"><span>Background Backdrop</span></div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:6, marginTop:6}}>
          {SWATCHES.map((sw, i) => (
            <button
              key={i}
              type="button"
              onClick={() => updateBgRemoverSettings({ bgType: sw.type, bgColor: sw.color })}
              style={{
                height: 36,
                borderRadius: 6,
                border: bgRemoverSettings.bgColor === sw.color && bgRemoverSettings.bgType === sw.type
                  ? '2px solid var(--accent-primary)'
                  : '1px solid var(--border-default)',
                background: sw.color === 'transparent'
                  ? 'repeating-conic-gradient(#555 0% 25%, #333 0% 50%) 50% / 10px 10px'
                  : sw.color,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 10,
                fontWeight: 600,
                color: sw.color === '#ffffff' ? '#000' : '#fff',
                boxShadow: '0 1px 3px rgba(0,0,0,0.2)'
              }}
              title={sw.label}
            >
              {sw.label.slice(0, 3)}
            </button>
          ))}
        </div>

        {/* Custom Color Input */}
        <div style={{display:'flex', alignItems:'center', gap:8, marginTop:8}}>
          <span style={{fontSize:11, color:'var(--text-muted)'}}>Custom Color:</span>
          <input
            type="color"
            value={bgRemoverSettings.bgColor.startsWith('#') ? bgRemoverSettings.bgColor : '#ffffff'}
            onChange={e => updateBgRemoverSettings({ bgType: 'color', bgColor: e.target.value })}
            style={{width:32, height:26, padding:0, border:'none', borderRadius:4, cursor:'pointer'}}
          />
          <span style={{fontSize:11, fontFamily:'monospace'}}>{bgRemoverSettings.bgColor}</span>
        </div>
      </div>

      {bgRemovedResult && (
        <div style={{
          marginTop: 14,
          padding: '12px',
          background: 'var(--bg-elevated)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid #f59e0b',
          width: '100%',
          maxWidth: '100%',
          boxSizing: 'border-box'
        }}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6}}>
            <span style={{color:'#f59e0b', fontWeight:600, fontSize:12}}>✓ Background Removed</span>
            <span style={{fontSize:11, color:'var(--text-muted)'}}>{bgRemovedResult.width} × {bgRemovedResult.height} px</span>
          </div>
          <div style={{display:'flex', flexWrap:'wrap', gap:4, marginBottom:10}}>
            {bgRemovedResult.changesApplied.map((c, i) => (
              <span key={i} style={{fontSize:10, padding:'2px 6px', borderRadius:4, background:'rgba(245,158,11,0.15)', color:'#f59e0b'}}>
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
                a.href = bgRemovedResult.url
                a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_cutout.png`
                a.click()
              }}
            >
              ⬇ Download Cutout PNG
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
              ⚡ Vectorize this Cutout →
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
