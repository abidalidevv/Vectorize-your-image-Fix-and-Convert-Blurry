import React, { useState } from 'react'
import { useAppStore } from '../store/appStore'
import {
  uploadImage,
  analyzeImage,
  preprocessImage,
  quantizeImage,
  vectorizeImage,
  exportSVG,
  exportPNG,
  deleteSession,
} from '../api/client'

export default function TopBar() {
  const {
    sessionId, stage, imageInfo, vectorResult,
    setStage, setImageInfo, setAnalysisResult,
    setPreprocessedUrl, setQuantized, setVectorResult,
    preprocessSettings, vectorizeSettings, numColors,
    setShowExportModal,
    reset,
  } = useAppStore()

  const [uploading, setUploading] = useState(false)

  const handleFileSelect = async (file: File) => {
    if (stage === 'uploading') return
    reset()
    setStage('uploading')
    try {
      const info = await uploadImage(file)
      setImageInfo(info)
      setStage('idle')
      // Auto-analyze
      const analysis = await analyzeImage(info.session_id)
      setAnalysisResult(analysis)
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const handleFilePicker = () => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.png,.jpg,.jpeg,.bmp,.webp'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) handleFileSelect(file)
    }
    input.click()
  }

  const handleReset = async () => {
    if (sessionId) {
      try { await deleteSession(sessionId) } catch {}
    }
    reset()
  }

  const handleExportSVG = async () => {
    if (!sessionId || !vectorResult) return
    setStage('exporting')
    try {
      const blob = await exportSVG(sessionId, true)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorizer'}_vector.svg`
      a.click()
      URL.revokeObjectURL(url)
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const handleExportPNG = async (scale: 1 | 2 | 4 | 8) => {
    if (!sessionId || !vectorResult) return
    setStage('exporting')
    try {
      const blob = await exportPNG(sessionId, scale)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorizer'}_${scale}x.png`
      a.click()
      URL.revokeObjectURL(url)
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || String(err))
    }
  }

  const isProcessing = ['uploading', 'analyzing', 'preprocessing', 'quantizing', 'vectorizing', 'exporting'].includes(stage)

  return (
    <div className="topbar">
      {/* Logo Rebranded to Vectorizer AI */}
      <div className="topbar-logo" title="Vectorizer AI — Local Raster to Vector Studio">
        <div className="topbar-logo-icon">V</div>
        <span className="topbar-logo-text">
          Vectorizer<span>AI</span>
        </span>
      </div>

      <div className="topbar-divider" />

      {/* Upload button */}
      <button
        className="btn btn-primary btn-sm topbar-upload-btn"
        onClick={handleFilePicker}
        disabled={isProcessing}
        data-tooltip="Upload PNG, JPG, BMP, or WebP"
        data-tooltip-pos="bottom"
      >
        {stage === 'uploading' ? (
          <><span className="spinner" style={{width:12,height:12}} /> <span className="btn-text">Uploading…</span></>
        ) : (
          <>⬆ <span className="btn-text">Upload</span><span className="btn-text-full"> Image</span></>
        )}
      </button>

      {sessionId && (
        <button
          className="btn btn-secondary btn-sm"
          onClick={handleReset}
          disabled={isProcessing}
          data-tooltip="Clear current image and start over"
          data-tooltip-pos="bottom"
        >
          ↺ <span className="btn-text">Reset</span>
        </button>
      )}

      {/* Export actions */}
      <div className="topbar-actions">
        {vectorResult && (
          <>
            {/* Prominent Export Button */}
            <button
              className="btn btn-primary btn-sm topbar-export-main-btn"
              onClick={() => setShowExportModal(true)}
              disabled={isProcessing}
              data-tooltip="Open Export & Download Dialog (SVG, PNG up to 8×)"
              data-tooltip-pos="bottom"
            >
              ⤓ <span className="btn-text">Export</span><span className="btn-text-full"> As…</span>
            </button>

            {/* Quick SVG download */}
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleExportSVG}
              disabled={isProcessing}
              data-tooltip="Quick Download Optimized SVG"
              data-tooltip-pos="bottom"
            >
              {stage === 'exporting' ? <span className="spinner" style={{width:12,height:12}} /> : null}
              ⬇ SVG
            </button>

            {/* Quick PNG download */}
            <button
              className="btn btn-secondary btn-sm"
              disabled={isProcessing}
              onClick={() => handleExportPNG(2)}
              data-tooltip="Quick Export 2× HD PNG"
              data-tooltip-pos="bottom"
            >
              ⬇ PNG (2×)
            </button>
          </>
        )}
      </div>
    </div>
  )
}
