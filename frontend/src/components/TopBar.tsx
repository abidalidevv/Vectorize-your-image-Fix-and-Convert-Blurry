import React, { useState } from 'react'
import { useAppStore } from '../store/appStore'
import {
  uploadImage,
  analyzeImage,
  exportSVG,
  exportPNG,
  deleteSession,
} from '../api/client'

export default function TopBar() {
  const {
    sessionId, stage, imageInfo, vectorResult, enhancedResult, bgRemovedResult, eraserResult,
    activeTool, setActiveTool,
    setStage, setImageInfo, setAnalysisResult,
    setShowExportModal,
    reset,
  } = useAppStore()

  const handleFileSelect = async (file: File) => {
    if (stage === 'uploading') return
    reset()
    setStage('uploading')
    try {
      const info = await uploadImage(file)
      setImageInfo(info)
      setStage('idle')
      try {
        const analysis = await analyzeImage(info.session_id)
        setAnalysisResult(analysis)
      } catch (analysisErr) {
        console.warn('Auto analysis note:', analysisErr)
      }
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

  const handleDownloadEnhanced = () => {
    if (!enhancedResult?.url) return
    const a = document.createElement('a')
    a.href = enhancedResult.url
    a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_enhanced.png`
    a.click()
  }

  const handleDownloadBgRemoved = () => {
    if (!bgRemovedResult?.url) return
    const a = document.createElement('a')
    a.href = bgRemovedResult.url
    a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_cutout.png`
    a.click()
  }

  const handleDownloadEraser = () => {
    if (!eraserResult?.url) return
    const a = document.createElement('a')
    a.href = eraserResult.url
    a.download = `${imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'}_inpainted.png`
    a.click()
  }

  const isProcessing = [
    'uploading', 'analyzing', 'preprocessing', 'quantizing',
    'vectorizing', 'enhancing', 'removing_bg', 'erasing', 'exporting'
  ].includes(stage)

  return (
    <div className="topbar">
      {/* Logo */}
      <div className="topbar-logo" title="Vectorizer AI Studio">
        <div className="topbar-logo-icon">V</div>
        <span className="topbar-logo-text">
          Vectorizer<span>AI</span>
        </span>
      </div>

      <div className="topbar-divider" />

      {/* ── Studio Multi-Tool Switcher ───────────────────────────────── */}
      <div className="topbar-mode-switcher" role="tablist" aria-label="Studio Mode">
        <button
          className={`mode-tab ${activeTool === 'vectorizer' ? 'active' : ''}`}
          onClick={() => setActiveTool('vectorizer')}
          title="Raster to Vector Tracing Studio"
        >
          <span className="mode-tab-icon">⚡</span>
          <span className="mode-tab-title">Vectorizer</span>
        </button>
        <button
          className={`mode-tab ${activeTool === 'enhancer' ? 'active' : ''}`}
          onClick={() => setActiveTool('enhancer')}
          title="Super-Resolution, Deblur, Sharpen & Enhance Studio"
        >
          <span className="mode-tab-icon">✨</span>
          <span className="mode-tab-title">Image Enhancer</span>
        </button>
        <button
          className={`mode-tab ${activeTool === 'bgremover' ? 'active' : ''}`}
          onClick={() => setActiveTool('bgremover')}
          title="Free AI & Local Background Remover"
        >
          <span className="mode-tab-icon">✂️</span>
          <span className="mode-tab-title">Remove BG</span>
        </button>
        <button
          className={`mode-tab ${activeTool === 'eraser' ? 'active' : ''}`}
          onClick={() => setActiveTool('eraser')}
          title="Magic Eraser & Object Removal Inpainting AI"
        >
          <span className="mode-tab-icon">🪄</span>
          <span className="mode-tab-title">Magic Eraser</span>
        </button>
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

      <a
        href="/documentation.html"
        target="_blank"
        rel="noopener"
        className="btn btn-secondary btn-sm"
        style={{textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 5}}
        data-tooltip="Open Master Documentation & Image Settings Guide"
        data-tooltip-pos="bottom"
      >
        📖 <span className="btn-text">Docs & Guide</span>
      </a>

      <a
        href="/diagnose.html"
        target="_blank"
        rel="noopener noreferrer"
        className="btn btn-secondary btn-sm"
        style={{textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 5, borderColor: 'rgba(16, 185, 129, 0.35)'}}
        data-tooltip="Open System, Hardware & Model Diagnostics Dashboard"
        data-tooltip-pos="bottom"
      >
        🩺 <span className="btn-text">Diagnose</span>
      </a>

      {/* Export & Download actions */}
      <div className="topbar-actions">
        {activeTool === 'vectorizer' && vectorResult && (
          <>
            <button
              className="btn btn-primary btn-sm topbar-export-main-btn"
              onClick={() => setShowExportModal(true)}
              disabled={isProcessing}
              data-tooltip="Open Export & Download Dialog (SVG, PNG up to 8×)"
              data-tooltip-pos="bottom"
            >
              ⤓ <span className="btn-text">Export</span><span className="btn-text-full"> As…</span>
            </button>

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

        {activeTool === 'enhancer' && enhancedResult && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleDownloadEnhanced}
            disabled={isProcessing}
            style={{background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'}}
            title="Download Enhanced High-Res PNG"
          >
            ⬇ Download Enhanced PNG ({enhancedResult.width}×{enhancedResult.height})
          </button>
        )}

        {activeTool === 'bgremover' && bgRemovedResult && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleDownloadBgRemoved}
            disabled={isProcessing}
            style={{background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'}}
            title="Download Cutout PNG"
          >
            ⬇ Download Cutout PNG ({bgRemovedResult.width}×{bgRemovedResult.height})
          </button>
        )}

        {activeTool === 'eraser' && eraserResult && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleDownloadEraser}
            disabled={isProcessing}
            style={{background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)'}}
            title="Download Clean Inpainted PNG"
          >
            ⬇ Download Clean PNG ({eraserResult.width}×{eraserResult.height})
          </button>
        )}
      </div>
    </div>
  )
}
