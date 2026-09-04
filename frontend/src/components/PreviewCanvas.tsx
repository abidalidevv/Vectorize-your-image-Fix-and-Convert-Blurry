import React, { useRef, useState, useEffect, useCallback } from 'react'
import { useAppStore } from '../store/appStore'
import type { ViewMode } from '../store/appStore'

const ZOOM_LEVELS = [0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 5.0, 10.0, 20.0]

export default function PreviewCanvas() {
  const {
    imageInfo, vectorResult, preprocessedUrl, quantizedUrl,
    viewMode, setViewMode, zoom, setZoom,
  } = useAppStore()

  const containerRef = useRef<HTMLDivElement>(null)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 })
  const [splitPos, setSplitPos] = useState(50)
  const [draggingSplit, setDraggingSplit] = useState(false)
  const [showSplit, setShowSplit] = useState(false)

  // Reset pan when image changes
  useEffect(() => {
    setPan({ x: 0, y: 0 })
    setZoom(1)
  }, [imageInfo?.session_id])

  // Determine which URL to show for current view
  const currentUrl = (() => {
    if (viewMode === 'vector' && vectorResult) return vectorResult.svg_url
    if (viewMode === 'enhanced') {
      if (quantizedUrl) return quantizedUrl
      if (preprocessedUrl) return preprocessedUrl
    }
    return imageInfo?.preview_url ?? null
  })()

  const isVector = viewMode === 'vector' && !!vectorResult

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const factor = e.deltaY < 0 ? 1.15 : 0.87
    setZoom(Math.min(20, Math.max(0.05, zoom * factor)))
  }, [zoom, setZoom])

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return
    setDragging(true)
    setLastMouse({ x: e.clientX, y: e.clientY })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (dragging) {
      setPan(p => ({
        x: p.x + (e.clientX - lastMouse.x),
        y: p.y + (e.clientY - lastMouse.y),
      }))
      setLastMouse({ x: e.clientX, y: e.clientY })
    }
    if (draggingSplit && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect()
      const pos = ((e.clientX - rect.left) / rect.width) * 100
      setSplitPos(Math.max(5, Math.min(95, pos)))
    }
  }

  const handleMouseUp = () => {
    setDragging(false)
    setDraggingSplit(false)
  }

  const zoomIn  = () => setZoom(Math.min(20, zoom * 1.4))
  const zoomOut = () => setZoom(Math.max(0.05, zoom / 1.4))
  const zoomFit = () => { setZoom(1); setPan({ x: 0, y: 0 }) }
  const zoomTo  = (z: number) => setZoom(z)

  const zoomPct = `${Math.round(zoom * 100)}%`

  if (!imageInfo) return null

  const viewTabs: { id: ViewMode; label: string; available: boolean }[] = [
    { id: 'original', label: 'Original', available: true },
    { id: 'enhanced', label: 'Enhanced', available: !!(preprocessedUrl || quantizedUrl) },
    { id: 'vector',   label: 'Vector',   available: !!vectorResult },
  ]

  const transformStyle: React.CSSProperties = {
    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
    transformOrigin: 'center center',
    transition: dragging ? 'none' : 'transform 0.05s ease',
  }

  return (
    <div
      className="preview-area checkerboard"
      ref={containerRef}
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ position: 'relative', flex: 1, minHeight: 0, overflow: 'hidden' }}
    >
      {/* View Mode Tabs */}
      <div className="preview-toolbar">
        {viewTabs.map(tab => (
          <button
            key={tab.id}
            className={`view-tab ${viewMode === tab.id ? 'active' : ''}`}
            onClick={() => tab.available && setViewMode(tab.id)}
            style={{ opacity: tab.available ? 1 : 0.35, cursor: tab.available ? 'pointer' : 'default' }}
            title={tab.available ? tab.label : `${tab.label} (not yet generated)`}
          >
            {tab.label}
          </button>
        ))}

        {vectorResult && imageInfo && (
          <>
            <div style={{width:1, height:16, background:'var(--border-default)', margin:'0 4px'}} />
            <button
              className={`view-tab ${showSplit ? 'active' : ''}`}
              onClick={() => setShowSplit(!showSplit)}
              title="Toggle split before/after view"
            >
              ⇔ Split
            </button>
          </>
        )}
      </div>

      {/* Main Preview */}
      {!showSplit ? (
        <div
          className="preview-viewport"
          style={{ width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center' }}
        >
          <div style={transformStyle}>
            {isVector ? (
              // Use <img> with SVG URL so we get true vector rendering
              <img
                src={currentUrl!}
                alt="Vector result"
                style={{
                  display: 'block',
                  maxWidth: 'none',
                  width: imageInfo.width,
                  height: imageInfo.height,
                  imageRendering: 'auto',
                }}
                draggable={false}
              />
            ) : (
              <img
                src={currentUrl!}
                alt="Preview"
                style={{
                  display: 'block',
                  maxWidth: 'none',
                  width: imageInfo.width,
                  height: imageInfo.height,
                  imageRendering: zoom >= 4 ? 'pixelated' : 'auto',
                }}
                draggable={false}
              />
            )}
          </div>
        </div>
      ) : (
        /* Split View */
        <div style={{ position:'relative', width:'100%', height:'100%', overflow:'hidden' }}>
          {/* Left side: original */}
          <div
            style={{
              position:'absolute', inset:0, overflow:'hidden',
              clipPath: `inset(0 ${100-splitPos}% 0 0)`,
            }}
          >
            <div style={{...transformStyle, width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>
              <img src={imageInfo.preview_url} alt="Original" style={{maxWidth:'none', width: imageInfo.width, height: imageInfo.height}} draggable={false} />
            </div>
          </div>

          {/* Right side: vector */}
          <div
            style={{
              position:'absolute', inset:0, overflow:'hidden',
              clipPath: `inset(0 0 0 ${splitPos}%)`,
            }}
          >
            <div style={{...transformStyle, width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center'}}>
              <img src={vectorResult?.svg_url} alt="Vector" style={{maxWidth:'none', width: imageInfo.width, height: imageInfo.height}} draggable={false} />
            </div>
          </div>

          {/* Divider handle */}
          <div
            style={{
              position:'absolute', top:0, bottom:0,
              left: `${splitPos}%`,
              width: 2,
              background: 'var(--accent-primary)',
              cursor: 'ew-resize',
              transform: 'translateX(-50%)',
              boxShadow: '0 0 8px var(--accent-glow)',
            }}
            onMouseDown={(e) => { e.stopPropagation(); setDraggingSplit(true) }}
          >
            <div style={{
              position:'absolute', top:'50%', left:'50%',
              transform:'translate(-50%,-50%)',
              width:20, height:20, borderRadius:'50%',
              background:'var(--accent-primary)',
              border:'2px solid white',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:10, color:'white', userSelect:'none',
            }}>⇔</div>
          </div>
        </div>
      )}

      {/* Zoom Controls */}
      <div className="zoom-controls">
        <div className="zoom-group">
          <button className="zoom-btn" onClick={zoomIn} title="Zoom in">+</button>
          <div className="zoom-display">{zoomPct}</div>
          <button className="zoom-btn" onClick={zoomOut} title="Zoom out">−</button>
        </div>
        <div className="zoom-group" style={{marginTop:4}}>
          {[['Fit', 1.0], ['1×', 1.0], ['2×', 2.0], ['5×', 5.0], ['10×', 10.0], ['20×', 20.0]].map(([label, val]) => (
            <button
              key={String(label)}
              className="zoom-btn"
              style={{fontSize:9, height:22}}
              onClick={() => {
                if (label === 'Fit') { zoomFit() } else { zoomTo(val as number) }
              }}
              title={`Zoom to ${label}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Vector badge */}
      {isVector && (
        <div style={{
          position:'absolute', bottom: 'var(--space-3)', left: 'var(--space-3)',
          background:'var(--success-bg)', border:'1px solid rgba(52,211,153,0.3)',
          color: 'var(--success)', padding:'3px 10px', borderRadius:'var(--radius-md)',
          fontSize:11, fontWeight:600, display:'flex', alignItems:'center', gap:4,
          pointerEvents:'none',
        }}>
          ◈ True Vector — {vectorResult?.stats.path_count} paths
        </div>
      )}
    </div>
  )
}

