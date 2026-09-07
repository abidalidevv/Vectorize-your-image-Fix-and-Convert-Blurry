import React, { useState, useEffect } from 'react'
import { useAppStore, StudioTool } from '../store/appStore'
import { exportSVG, exportPNG } from '../api/client'

export default function ExportModal() {
  const {
    sessionId, imageInfo, vectorResult, enhancedResult, bgRemovedResult, eraserResult,
    activeTool, setActiveTool, setVectorizeSourceStage,
    showExportModal, setShowExportModal,
  } = useAppStore()

  const [selectedTool, setSelectedTool] = useState<StudioTool>(activeTool)
  const [activeTab, setActiveTab] = useState<'svg' | 'png'>('svg')
  const [pngScale, setPngScale] = useState<1 | 2 | 4 | 8>(2)
  const [svgOptimize, setSvgOptimize] = useState(true)
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

  // Sync selected tool with active tool or available result when modal opens
  useEffect(() => {
    if (showExportModal) {
      if (activeTool === 'vectorizer' && vectorResult) {
        setSelectedTool('vectorizer')
      } else if (activeTool === 'enhancer' && enhancedResult) {
        setSelectedTool('enhancer')
      } else if (activeTool === 'bgremover' && bgRemovedResult) {
        setSelectedTool('bgremover')
      } else if (activeTool === 'eraser' && eraserResult) {
        setSelectedTool('eraser')
      } else {
        if (vectorResult) setSelectedTool('vectorizer')
        else if (enhancedResult) setSelectedTool('enhancer')
        else if (bgRemovedResult) setSelectedTool('bgremover')
        else if (eraserResult) setSelectedTool('eraser')
        else setSelectedTool(activeTool)
      }
    }
  }, [showExportModal, activeTool, vectorResult, enhancedResult, bgRemovedResult, eraserResult])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowExportModal(false)
    }
    if (showExportModal) {
      window.addEventListener('keydown', handleKeyDown)
    }
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [showExportModal, setShowExportModal])

  if (!showExportModal) return null

  const baseName = imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'image'
  const origW = imageInfo?.width ?? 300
  const origH = imageInfo?.height ?? 300

  const handleDownloadSVG = async () => {
    if (!sessionId || !vectorResult) return
    setDownloading(true)
    try {
      const blob = await exportSVG(sessionId, svgOptimize)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${baseName}_vector.svg`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert('Export failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setDownloading(false)
    }
  }

  const handleCopySVG = async () => {
    if (!vectorResult) return
    try {
      const resp = await fetch(vectorResult.svg_url)
      const text = await resp.text()
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    } catch (err) {
      alert('Failed to copy SVG: ' + String(err))
    }
  }

  const handleDownloadPNG = async () => {
    if (!sessionId || !vectorResult) return
    setDownloading(true)
    try {
      const blob = await exportPNG(sessionId, pngScale)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${baseName}_${pngScale}x.png`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err: any) {
      alert('PNG export failed: ' + (err?.response?.data?.detail || err.message))
    } finally {
      setDownloading(false)
    }
  }

  const handleDownloadEnhanced = () => {
    if (!enhancedResult?.url) return
    const a = document.createElement('a')
    a.href = enhancedResult.url
    a.download = `${baseName}_enhanced.png`
    a.click()
  }

  const handleDownloadBgRemoved = () => {
    if (!bgRemovedResult?.url) return
    const a = document.createElement('a')
    a.href = bgRemovedResult.url
    a.download = `${baseName}_cutout.png`
    a.click()
  }

  const handleDownloadEraser = () => {
    if (!eraserResult?.url) return
    const a = document.createElement('a')
    a.href = eraserResult.url
    a.download = `${baseName}_inpainted.png`
    a.click()
  }

  const handleJumpToVectorizer = () => {
    setVectorizeSourceStage('auto')
    setActiveTool('vectorizer')
    setShowExportModal(false)
  }

  const availableOutputs = [
    { tool: 'vectorizer' as const, label: 'Vectorizer SVG', ready: !!vectorResult, icon: '⚡' },
    { tool: 'enhancer' as const, label: 'Image Enhancer', ready: !!enhancedResult, icon: '✨' },
    { tool: 'bgremover' as const, label: 'Cutout PNG', ready: !!bgRemovedResult, icon: '✂️' },
    { tool: 'eraser' as const, label: 'Magic Eraser', ready: !!eraserResult, icon: '🪄' },
  ]
  const readyCount = availableOutputs.filter(o => o.ready).length

  return (
    <div className="modal-backdrop" onClick={() => setShowExportModal(false)}>
      <div className="modal-content export-modal" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">⤓</span>
            <div>
              <h3>
                {selectedTool === 'vectorizer' && 'Export Vector Image'}
                {selectedTool === 'enhancer' && 'Export Enhanced Image'}
                {selectedTool === 'bgremover' && 'Export Background Cutout'}
                {selectedTool === 'eraser' && 'Export Inpainted Image'}
              </h3>
              <p className="modal-subtitle">
                {selectedTool === 'vectorizer' && 'Choose format, resolution, and optimization settings'}
                {selectedTool === 'enhancer' && 'Download super-resolution upscaled & restored high-definition PNG'}
                {selectedTool === 'bgremover' && 'Download cutout with transparent background or trace to vector'}
                {selectedTool === 'eraser' && 'Download clean photo with unwanted objects removed'}
              </p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={() => setShowExportModal(false)} title="Close (Esc)">
            ✕
          </button>
        </div>

        {/* Multi-Tool Output Switcher if more than one result exists */}
        {readyCount > 1 && (
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 6,
            padding: '10px 20px',
            background: 'var(--bg-elevated)',
            borderBottom: '1px solid var(--border-subtle)',
            alignItems: 'center',
          }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Output:
            </span>
            {availableOutputs.filter(o => o.ready).map(o => (
              <button
                key={o.tool}
                type="button"
                onClick={() => setSelectedTool(o.tool)}
                style={{
                  padding: '4px 10px',
                  fontSize: 11.5,
                  fontWeight: selectedTool === o.tool ? 600 : 500,
                  borderRadius: 'var(--radius-sm)',
                  border: selectedTool === o.tool ? '1px solid var(--accent-primary)' : '1px solid var(--border-default)',
                  background: selectedTool === o.tool ? 'var(--accent-subtle)' : 'var(--bg-base)',
                  color: selectedTool === o.tool ? 'var(--accent-primary)' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                }}
              >
                <span>{o.icon}</span>
                <span>{o.label}</span>
              </button>
            ))}
          </div>
        )}

        {/* ── TOOL 1: VECTORIZER EXPORT ─────────────────────────── */}
        {selectedTool === 'vectorizer' && (
          vectorResult ? (
            <>
              {/* Format Selector Tabs */}
              <div className="export-tabs">
                <button
                  className={`export-tab-btn ${activeTab === 'svg' ? 'active' : ''}`}
                  onClick={() => setActiveTab('svg')}
                >
                  <span className="export-tab-badge">Recommended</span>
                  <span className="export-tab-title">SVG Vector</span>
                  <span className="export-tab-desc">Scalable, crisp at infinite zoom</span>
                </button>
                <button
                  className={`export-tab-btn ${activeTab === 'png' ? 'active' : ''}`}
                  onClick={() => setActiveTab('png')}
                >
                  <span className="export-tab-badge">Raster</span>
                  <span className="export-tab-title">High-Res PNG</span>
                  <span className="export-tab-desc">Rendered up to 8× (300+ DPI)</span>
                </button>
              </div>

              {/* Tab 1: SVG Content */}
              {activeTab === 'svg' && (
                <div className="export-tab-content">
                  <div className="export-info-card">
                    <div className="export-stat-row">
                      <span className="export-stat-label">File Type</span>
                      <span className="export-stat-val">Scalable Vector Graphics (.svg)</span>
                    </div>
                    <div className="export-stat-row">
                      <span className="export-stat-label">Paths / Layers</span>
                      <span className="export-stat-val">{vectorResult.stats.path_count} paths • {vectorResult.layers.length} color groups</span>
                    </div>
                    <div className="export-stat-row">
                      <span className="export-stat-label">Dimensions</span>
                      <span className="export-stat-val">{origW} × {origH} px (Infinite Scalable)</span>
                    </div>
                    <div className="export-stat-row">
                      <span className="export-stat-label">File Size</span>
                      <span className="export-stat-val">~{(vectorResult.stats.file_size_bytes / 1024).toFixed(1)} KB</span>
                    </div>
                  </div>

                  <label className="checkbox-label" style={{ marginTop: 16 }}>
                    <input
                      type="checkbox"
                      checked={svgOptimize}
                      onChange={e => setSvgOptimize(e.target.checked)}
                    />
                    <span>Clean & optimize SVG paths (removes redundant metadata)</span>
                  </label>

                  <div className="export-action-row" style={{ marginTop: 20 }}>
                    <button
                      className="btn btn-primary btn-lg"
                      style={{ flex: 1 }}
                      onClick={handleDownloadSVG}
                      disabled={downloading}
                    >
                      {downloading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '⤓'}
                      Download SVG ({baseName}_vector.svg)
                    </button>
                    <button
                      className="btn btn-secondary btn-lg"
                      onClick={handleCopySVG}
                      title="Copy raw SVG text code to clipboard"
                    >
                      {copied ? '✓ Copied!' : '📋 Copy Code'}
                    </button>
                  </div>
                </div>
              )}

              {/* Tab 2: PNG Content */}
              {activeTab === 'png' && (
                <div className="export-tab-content">
                  <div className="export-scale-selector">
                    <label className="export-section-label">Select Resolution / Scale Multiplier:</label>
                    <div className="scale-pill-grid">
                      {[
                        { scale: 1, label: '1× (Original)', desc: `${origW} × ${origH} px` },
                        { scale: 2, label: '2× (HD)', desc: `${origW * 2} × ${origH * 2} px` },
                        { scale: 4, label: '4× (Ultra HD)', desc: `${origW * 4} × ${origH * 4} px` },
                        { scale: 8, label: '8× (Print / 300 DPI)', desc: `${origW * 8} × ${origH * 8} px` },
                      ].map(item => (
                        <button
                          key={item.scale}
                          className={`scale-pill-btn ${pngScale === item.scale ? 'active' : ''}`}
                          onClick={() => setPngScale(item.scale as any)}
                        >
                          <span className="scale-pill-title">{item.label}</span>
                          <span className="scale-pill-desc">{item.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="export-action-row" style={{ marginTop: 24 }}>
                    <button
                      className="btn btn-primary btn-lg"
                      style={{ width: '100%' }}
                      onClick={handleDownloadPNG}
                      disabled={downloading}
                    >
                      {downloading ? <span className="spinner" style={{ width: 14, height: 14 }} /> : '⤓'}
                      Download {pngScale}× PNG ({origW * pngScale} × {origH * pngScale} px)
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={{ padding: '32px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>⚡</div>
              <h4 style={{ margin: '0 0 6px 0', fontSize: 15, color: 'var(--text-primary)' }}>No Vector Graphic Ready</h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                Click the "Vectorize" button in the left panel to trace your image into scalable SVG paths.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setActiveTool('vectorizer')
                  setShowExportModal(false)
                }}
              >
                Go to Vectorizer
              </button>
            </div>
          )
        )}

        {/* ── TOOL 2: ENHANCER EXPORT ───────────────────────────── */}
        {selectedTool === 'enhancer' && (
          enhancedResult ? (
            <div className="export-tab-content" style={{ padding: '20px 24px' }}>
              <div className="export-info-card">
                <div className="export-stat-row">
                  <span className="export-stat-label">File Type</span>
                  <span className="export-stat-val">Enhanced Portable Network Graphics (.png)</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Enhanced Dimensions</span>
                  <span className="export-stat-val">{enhancedResult.width} × {enhancedResult.height} px</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Applied Changes</span>
                  <span className="export-stat-val" style={{ maxWidth: 280, textAlign: 'right' }}>
                    {enhancedResult.changesApplied.join(' • ') || 'Super-Resolution + Clarity'}
                  </span>
                </div>
              </div>

              <div className="export-action-row" style={{ marginTop: 24 }}>
                <button
                  type="button"
                  className="btn btn-primary btn-lg full-width"
                  onClick={handleDownloadEnhanced}
                  style={{
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    boxShadow: '0 4px 16px rgba(16, 185, 129, 0.4)',
                  }}
                >
                  ⤓ Download Enhanced PNG ({enhancedResult.width} × {enhancedResult.height} px)
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: '32px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>✨</div>
              <h4 style={{ margin: '0 0 6px 0', fontSize: 15, color: 'var(--text-primary)' }}>No Enhanced Image Ready</h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                Click "Enhance Image" in the left panel to run AI super-resolution and clarity improvements.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setActiveTool('enhancer')
                  setShowExportModal(false)
                }}
              >
                Go to Image Enhancer
              </button>
            </div>
          )
        )}

        {/* ── TOOL 3: BG REMOVER EXPORT ─────────────────────────── */}
        {selectedTool === 'bgremover' && (
          bgRemovedResult ? (
            <div className="export-tab-content" style={{ padding: '20px 24px' }}>
              <div className="export-info-card">
                <div className="export-stat-row">
                  <span className="export-stat-label">File Type</span>
                  <span className="export-stat-val">Cutout PNG with Alpha Transparency (.png)</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Dimensions</span>
                  <span className="export-stat-val">{bgRemovedResult.width} × {bgRemovedResult.height} px</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Background Status</span>
                  <span className="export-stat-val" style={{ color: 'var(--success)' }}>✓ Transparent RGBA Alpha</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Processing</span>
                  <span className="export-stat-val" style={{ maxWidth: 280, textAlign: 'right' }}>
                    {bgRemovedResult.changesApplied.join(' • ') || 'Edge Defringing & Color Decontamination'}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 24 }}>
                <button
                  type="button"
                  className="btn btn-primary btn-lg full-width"
                  onClick={handleDownloadBgRemoved}
                  style={{
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    boxShadow: '0 4px 16px rgba(245, 158, 11, 0.4)',
                  }}
                >
                  ⤓ Download Cutout PNG ({bgRemovedResult.width} × {bgRemovedResult.height} px)
                </button>

                <button
                  type="button"
                  className="btn btn-secondary full-width"
                  onClick={handleJumpToVectorizer}
                  style={{ padding: '10px 14px', fontSize: 12.5 }}
                >
                  ◈ Trace Cutout to Vector (Jump to Vectorizer) →
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: '32px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>✂️</div>
              <h4 style={{ margin: '0 0 6px 0', fontSize: 15, color: 'var(--text-primary)' }}>No Cutout Ready</h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                Click "Remove Background" in the left panel to remove the background and isolate the subject.
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setActiveTool('bgremover')
                  setShowExportModal(false)
                }}
              >
                Go to Remove BG
              </button>
            </div>
          )
        )}

        {/* ── TOOL 4: MAGIC ERASER EXPORT ───────────────────────── */}
        {selectedTool === 'eraser' && (
          eraserResult ? (
            <div className="export-tab-content" style={{ padding: '20px 24px' }}>
              <div className="export-info-card">
                <div className="export-stat-row">
                  <span className="export-stat-label">File Type</span>
                  <span className="export-stat-val">Inpainted Portable Network Graphics (.png)</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Dimensions</span>
                  <span className="export-stat-val">{eraserResult.width} × {eraserResult.height} px</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Inpainting Result</span>
                  <span className="export-stat-val" style={{ color: 'var(--success)' }}>✓ Unwanted Objects Removed</span>
                </div>
                <div className="export-stat-row">
                  <span className="export-stat-label">Processing</span>
                  <span className="export-stat-val" style={{ maxWidth: 280, textAlign: 'right' }}>
                    {eraserResult.changesApplied.join(' • ') || 'Neural Mask Inpainting'}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 24 }}>
                <button
                  type="button"
                  className="btn btn-primary btn-lg full-width"
                  onClick={handleDownloadEraser}
                  style={{
                    background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                    boxShadow: '0 4px 16px rgba(244, 63, 94, 0.4)',
                  }}
                >
                  ⤓ Download Clean PNG ({eraserResult.width} × {eraserResult.height} px)
                </button>

                <button
                  type="button"
                  className="btn btn-secondary full-width"
                  onClick={handleJumpToVectorizer}
                  style={{ padding: '10px 14px', fontSize: 12.5 }}
                >
                  ◈ Trace Clean Image to Vector (Jump to Vectorizer) →
                </button>
              </div>
            </div>
          ) : (
            <div style={{ padding: '32px 24px', textAlign: 'center' }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>🪄</div>
              <h4 style={{ margin: '0 0 6px 0', fontSize: 15, color: 'var(--text-primary)' }}>No Inpainted Image Ready</h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 16px 0', lineHeight: 1.5 }}>
                Use Draw Mask to paint over an unwanted object, then click "Erase Object".
              </p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setActiveTool('eraser')
                  setShowExportModal(false)
                }}
              >
                Go to Magic Eraser
              </button>
            </div>
          )
        )}
      </div>
    </div>
  )
}
