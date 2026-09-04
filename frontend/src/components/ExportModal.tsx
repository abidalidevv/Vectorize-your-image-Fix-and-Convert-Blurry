import React, { useState, useEffect } from 'react'
import { useAppStore } from '../store/appStore'
import { exportSVG, exportPNG } from '../api/client'

export default function ExportModal() {
  const {
    sessionId, imageInfo, vectorResult, stage, setStage,
    showExportModal, setShowExportModal,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<'svg' | 'png'>('svg')
  const [pngScale, setPngScale] = useState<1 | 2 | 4 | 8>(2)
  const [svgOptimize, setSvgOptimize] = useState(true)
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

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

  if (!showExportModal || !sessionId || !vectorResult) return null

  const baseName = imageInfo?.filename?.replace(/\.\w+$/, '') ?? 'vectorizer'

  const handleDownloadSVG = async () => {
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

  const origW = imageInfo?.width ?? 300
  const origH = imageInfo?.height ?? 300

  return (
    <div className="modal-backdrop" onClick={() => setShowExportModal(false)}>
      <div className="modal-content export-modal" onClick={e => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <span className="modal-icon">⤓</span>
            <div>
              <h3>Export Vector Image</h3>
              <p className="modal-subtitle">Choose format, resolution, and optimization settings</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={() => setShowExportModal(false)} title="Close (Esc)">
            ✕
          </button>
        </div>

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
                <span className="export-stat-val">{origW} × {origH} px (Scalable)</span>
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
              <span>Clean & optimize SVG paths (removes redundant metadata & comments)</span>
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
      </div>
    </div>
  )
}
