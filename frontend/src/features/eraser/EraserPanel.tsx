import React from 'react'
import { useAppStore } from '../../store/appStore'
import { inpaintImage } from '../../api/client'

function Slider({ label, value, min, max, step = 1, onChange, disabled = false, unit = 'px' }: {
  label: string; value: number; min: number; max: number
  step?: number; onChange: (v: number) => void; disabled?: boolean; unit?: string
}) {
  return (
    <div className="control-group">
      <div className="control-label">
        <span>{label}</span>
        <span className="value-display">{value}{unit}</span>
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

export default function EraserPanel() {
  const {
    sessionId, stage, imageInfo,
    eraserSettings, updateEraserSettings,
    eraserResult, setEraserResult,
    eraserMaskData, setEraserMaskData,
    setStage, setViewMode, setActiveTool, setVectorizeSourceStage,
  } = useAppStore()

  const isProcessing = stage === 'erasing'
  const isUltra = eraserSettings.quality === 'ultra' || eraserSettings.modelTier === 'pro'

  const handleErase = async () => {
    if (!sessionId) return
    if (!eraserMaskData) {
      alert('Please brush over the object or text you want to remove first!')
      return
    }

    setStage('erasing')
    try {
      const res = await inpaintImage({
        session_id: sessionId,
        mask_data: eraserMaskData,
        quality: eraserSettings.quality,
        model_tier: eraserSettings.modelTier,
        dilate_radius: eraserSettings.dilateRadius,
        method: eraserSettings.method,
      })
      setEraserResult({
        url: res.preview_url,
        width: res.width,
        height: res.height,
        changesApplied: res.changes_applied,
      })
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const handleClearMask = () => {
    setEraserMaskData(null)
    // Dispatch custom event to notify PreviewCanvas to clear its mask canvas
    window.dispatchEvent(new CustomEvent('vectorforge:clear_eraser_mask'))
  }

  return (
    <div className="panel-section-content">
      {/* Informative Tip Card */}
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{ fontSize: 14 }}>🪄</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-primary)' }}>
            Magic Eraser & Inpainting
          </span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.45 }}>
          Brush directly over unwanted objects, people, text, logos, or watermarks. LaMa AI will synthesize and reconstruct the background seamlessly.
        </div>
      </div>

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
            onClick={() => updateEraserSettings({ quality: 'fast', modelTier: 'default' })}
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
            title="Fast LaMa Inpainting neural network"
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
              Fast LaMa AI
            </span>
          </button>

          <button
            type="button"
            className={`tier-btn ${isUltra ? 'active-pro' : ''}`}
            onClick={() => updateEraserSettings({ quality: 'ultra', modelTier: 'pro' })}
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
            title="Pro LaMa Inpainting with high-fidelity multi-scale edge blending"
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
              LaMa + Blend
            </span>
          </button>
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, lineHeight: 1.4 }}>
          {isUltra
            ? '👑 Pro Mode: Deep LaMa FFC reconstruction with multi-scale Poisson boundary blending.'
            : '⚡ Standard Mode: Ultra-fast (~1–2s) Large Mask Inpainting (LaMa) CPU inference.'}
        </div>
      </div>

      {/* Brush Settings */}
      <div className="control-group">
        <div className="control-label">
          <span>Brush Size</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {/* Live circular preview of brush */}
            <div style={{
              width: Math.min(24, Math.max(8, eraserSettings.brushSize / 2)),
              height: Math.min(24, Math.max(8, eraserSettings.brushSize / 2)),
              borderRadius: '50%',
              background: 'rgba(244, 63, 94, 0.8)',
              border: '1px solid white',
            }} />
            <span className="value-display">{eraserSettings.brushSize}px</span>
          </div>
        </div>
        <input
          type="range" min={5} max={120} step={2}
          value={eraserSettings.brushSize}
          onChange={(e) => updateEraserSettings({ brushSize: parseInt(e.target.value, 10) })}
          disabled={isProcessing}
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          {[15, 30, 50, 80].map(sz => (
            <button
              key={sz}
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ flex: 1, padding: '4px 0', fontSize: 11 }}
              onClick={() => updateEraserSettings({ brushSize: sz })}
            >
              {sz}px
            </button>
          ))}
        </div>
      </div>

      <Slider
        label="Edge Expansion (Mask Margin)"
        value={eraserSettings.dilateRadius}
        min={0} max={25} step={1}
        unit="px"
        onChange={v => updateEraserSettings({ dilateRadius: v })}
        disabled={isProcessing}
      />
      <div style={{ fontSize: 10.5, color: 'var(--text-muted)', marginTop: -6, marginBottom: 12 }}>
        Expands the brush stroke slightly to eliminate halos around the removed object.
      </div>

      {/* Mask Action Buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={handleClearMask}
          disabled={isProcessing || !eraserMaskData}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
        >
          <span>↺</span>
          <span>Clear Mask</span>
        </button>

        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={() => window.dispatchEvent(new CustomEvent('vectorforge:undo_eraser_mask'))}
          disabled={isProcessing || !eraserMaskData}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
        >
          <span>↩</span>
          <span>Undo Stroke</span>
        </button>
      </div>

      {/* Main Erase Action Button */}
      <button
        type="button"
        className="btn btn-primary full-width"
        onClick={handleErase}
        disabled={isProcessing || !eraserMaskData}
        style={{
          height: 42,
          fontSize: 13.5,
          fontWeight: 600,
          background: !eraserMaskData
            ? 'var(--bg-elevated)'
            : isUltra
              ? 'linear-gradient(135deg, #ec4899 0%, #a855f7 100%)'
              : 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
          color: !eraserMaskData ? 'var(--text-muted)' : '#ffffff',
          boxShadow: eraserMaskData
            ? '0 4px 16px rgba(244, 63, 94, 0.4)'
            : 'none',
          cursor: (isProcessing || !eraserMaskData) ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
        }}
      >
        {isProcessing ? (
          <><span className="spinner" style={{ width: 15, height: 15 }} /> Erasing Unwanted Area…</>
        ) : !eraserMaskData ? (
          '🖌️ Paint Over Object First'
        ) : isUltra ? (
          '👑 Erase Object (Pro Inpaint)'
        ) : (
          '🪄 Erase Object (Magic Eraser)'
        )}
      </button>

      {/* Result Card */}
      {eraserResult && (
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
            <span style={{ color: 'var(--success)', fontWeight: 600, fontSize: 12 }}>✓ Object Removed</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{eraserResult.width} × {eraserResult.height} px</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 10 }}>
            {eraserResult.changesApplied.map((c, i) => (
              <span key={i} style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: 'rgba(16,185,129,0.15)', color: '#10b981' }}>
                {c}
              </span>
            ))}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%', boxSizing: 'border-box' }}>
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
                a.href = eraserResult.url
                a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_inpainted.png`
                a.click()
              }}
            >
              ⬇ Download Clean PNG
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
