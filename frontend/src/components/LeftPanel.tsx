import React, { useState } from 'react'
import { useAppStore } from '../store/appStore'
import VectorizerPanel from '../features/vectorizer/VectorizerPanel'
import EnhancerPanel from '../features/enhancer/EnhancerPanel'
import BgRemoverPanel from '../features/bg_remover/BgRemoverPanel'
import EraserPanel from '../features/eraser/EraserPanel'
import { vectorizeImage, enhanceImage, removeBackground, inpaintImage } from '../api/client'

export default function LeftPanel() {
  const {
    sessionId, imageInfo, stage, errorMessage, activeTool,
    vectorizeSettings, vectorizeSourceStage, setVectorResult,
    enhancerSettings, setEnhancedResult,
    bgRemoverSettings, setBgRemovedResult,
    eraserSettings, eraserMaskData, setEraserMaskData, setEraserResult,
    setStage, setViewMode,
  } = useAppStore()

  const [imageInfoOpen, setImageInfoOpen] = useState(false)

  const hasImage = !!imageInfo
  const isProcessing = ['preprocessing', 'quantizing', 'vectorizing', 'enhancing', 'removing_bg', 'erasing'].includes(stage)

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
      })
      setEnhancedResult({
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
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

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
      setEraserMaskData(null)
      window.dispatchEvent(new CustomEvent('vectorforge:clear_eraser_mask'))
      setViewMode('enhanced')
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  return (
    <div className="left-panel">
      <div className="panel-scroll">
        {/* Common Image Info Section */}
        {hasImage && (
          <div className="panel-section">
            <div className="panel-section-header" onClick={() => setImageInfoOpen(!imageInfoOpen)}>
              <span className="panel-section-title">Image Info</span>
              <span className={`panel-section-chevron ${imageInfoOpen ? 'open' : ''}`}>▶</span>
            </div>
            {imageInfoOpen && (
              <div className="panel-section-content">
                <div className="image-info-card">
                  <div className="image-info-row">
                    <span className="image-info-label">File</span>
                    <span className="image-info-value" style={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
              </div>
            )}
          </div>
        )}

        {/* Dedicated Tool Panels */}
        {hasImage && activeTool === 'vectorizer' && <VectorizerPanel />}
        {hasImage && activeTool === 'enhancer' && <EnhancerPanel />}
        {hasImage && activeTool === 'bgremover' && <BgRemoverPanel />}
        {hasImage && activeTool === 'eraser' && <EraserPanel />}

        {/* Global Error Banner */}
        {stage === 'error' && (
          <div className="alert alert-error" style={{ margin: '8px var(--space-4)' }}>
            ⚠ {errorMessage || 'An error occurred'}
          </div>
        )}
      </div>

      {/* Pinned Bottom Action Button Bar */}
      {hasImage && (
        <div className="panel-bottom-bar">
          {activeTool === 'vectorizer' && (
            <button
              type="button"
              className="btn btn-primary full-width"
              onClick={handleVectorize}
              disabled={isProcessing}
              style={{
                height: 42,
                fontSize: 13.5,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
                boxShadow: '0 4px 14px rgba(79, 70, 229, 0.4)',
                cursor: isProcessing ? 'not-allowed' : 'pointer'
              }}
            >
              {stage === 'vectorizing' ? (
                <><span className="spinner" style={{ width: 15, height: 15 }} /> Vectorizing…</>
              ) : (
                '◈ Vectorize'
              )}
            </button>
          )}

          {activeTool === 'enhancer' && (
            <button
              type="button"
              className="btn btn-primary full-width"
              onClick={handleEnhance}
              disabled={isProcessing}
              style={{
                height: 42,
                fontSize: 13.5,
                fontWeight: 600,
                background: (enhancerSettings.quality === 'ultra' || enhancerSettings.modelTier === 'pro')
                  ? 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)'
                  : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                boxShadow: (enhancerSettings.quality === 'ultra' || enhancerSettings.modelTier === 'pro')
                  ? '0 4px 16px rgba(236, 72, 153, 0.4)'
                  : '0 4px 14px rgba(16, 185, 129, 0.4)',
                cursor: isProcessing ? 'not-allowed' : 'pointer'
              }}
            >
              {stage === 'enhancing' ? (
                <><span className="spinner" style={{ width: 15, height: 15 }} /> Enhancing Image…</>
              ) : (
                '◈ Enhance Image'
              )}
            </button>
          )}

          {activeTool === 'bgremover' && (
            <button
              type="button"
              className="btn btn-primary full-width"
              onClick={handleRemoveBg}
              disabled={isProcessing}
              style={{
                height: 42,
                fontSize: 13.5,
                fontWeight: 600,
                background: (bgRemoverSettings.quality === 'ultra' || bgRemoverSettings.modelTier === 'pro')
                  ? 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)'
                  : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                boxShadow: (bgRemoverSettings.quality === 'ultra' || bgRemoverSettings.modelTier === 'pro')
                  ? '0 4px 16px rgba(236, 72, 153, 0.4)'
                  : '0 4px 14px rgba(245, 158, 11, 0.4)',
                cursor: isProcessing ? 'not-allowed' : 'pointer'
              }}
            >
              {stage === 'removing_bg' ? (
                <><span className="spinner" style={{ width: 15, height: 15 }} /> Removing Background…</>
              ) : (
                '◈ Remove Background'
              )}
            </button>
          )}

          {activeTool === 'eraser' && (
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
                  : (eraserSettings.quality === 'ultra' || eraserSettings.modelTier === 'pro')
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
              {stage === 'erasing' ? (
                <><span className="spinner" style={{ width: 15, height: 15 }} /> Erasing Unwanted Area…</>
              ) : !eraserMaskData ? (
                'Paint Over Object First'
              ) : (
                '◈ Erase Object'
              )}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
