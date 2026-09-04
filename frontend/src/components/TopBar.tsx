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
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorforge'}_vector.svg`
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
      a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorforge'}_${scale}x.png`
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
      {/* Logo */}
      <div className="topbar-logo">
        <div className="topbar-logo-icon">V</div>
        <span className="topbar-logo-text">
          Vector<span>Forge</span><span className="topbar-logo-suffix"> AI</span>
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

      <div className="topbar-actions">
        {vectorResult && (
          <>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleExportSVG}
              disabled={isProcessing}
              data-tooltip="Download optimized SVG vector file"
              data-tooltip-pos="bottom"
            >
              {stage === 'exporting' ? <span className="spinner" style={{width:12,height:12}} /> : null}
              ⬇ SVG
            </button>

            <button
              className="btn btn-secondary btn-sm"
              disabled={isProcessing}
              onClick={() => handleExportPNG(1)}
              data-tooltip="Export PNG at original size"
              data-tooltip-pos="bottom"
            >
              ⬇ PNG
            </button>

            <div className="topbar-png-scales">
              <button
                className="btn btn-ghost btn-sm btn-scale"
                disabled={isProcessing}
                onClick={() => handleExportPNG(2)}
                data-tooltip="Export PNG at 2× resolution"
                data-tooltip-pos="bottom"
              >2×</button>
              <button
                className="btn btn-ghost btn-sm btn-scale"
                disabled={isProcessing}
                onClick={() => handleExportPNG(4)}
                data-tooltip="Export PNG at 4× resolution"
                data-tooltip-pos="bottom"
              >4×</button>
              <button
                className="btn btn-ghost btn-sm btn-scale"
                disabled={isProcessing}
                onClick={() => handleExportPNG(8)}
                data-tooltip="Export PNG at 8× resolution"
                data-tooltip-pos="bottom"
                data-tooltip-align="right"
              >8×</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

