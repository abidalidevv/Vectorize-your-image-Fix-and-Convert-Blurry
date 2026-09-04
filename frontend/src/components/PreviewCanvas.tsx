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

  // Non-passive wheel event listener to prevent browser page zoom (Ctrl+Wheel and trackpad pinch)
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const handleCanvasWheel = (e: WheelEvent) => {
      // Always prevent default page scroll / page zoom
      e.preventDefault()
      e.stopPropagation()

      const rect = el.getBoundingClientRect()
      const mouseX = e.clientX - rect.left - rect.width / 2
      const mouseY = e.clientY - rect.top - rect.height / 2

      const factor = e.deltaY < 0 ? 1.18 : 0.85

      setZoom((prevZoom: number) => {
        const nextZoom = Math.min(20, Math.max(0.05, prevZoom * factor))
        // Smooth focal-point zooming (centered on cursor)
        setPan(prevPan => ({
          x: mouseX - (mouseX - prevPan.x) * (nextZoom / prevZoom),
          y: mouseY - (mouseY - prevPan.y) * (nextZoom / prevZoom),
        }))
        return nextZoom
      })
    }

    // Global listener to prevent whole-page zoom if user holds Ctrl while scrolling over the app
    const handleGlobalWheel = (e: WheelEvent) => {
      if (e.ctrlKey) {
        e.preventDefault()
      }
    }

    el.addEventListener('wheel', handleCanvasWheel, { passive: false })
    window.addEventListener('wheel', handleGlobalWheel, { passive: false })

    return () => {
      el.removeEventListener('wheel', handleCanvasWheel)
      window.removeEventListener('wheel', handleGlobalWheel)
    }
  }, [setZoom])

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

  const zoomIn  = () => setZoom((z: number) => Math.min(20, z * 1.4))
  const zoomOut = () => setZoom((z: number) => Math.max(0.05, z / 1.4))
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
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{
        position: 'relative',
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
        touchAction: 'none',
      }}
    >
      {/* View Mode Tabs */}
      <div className="preview-toolbar">
        {viewTabs.map(tab => (
          <button
            key={tab.id}
            className={`view-tab ${!showSplit && viewMode === tab.id ? 'active' : ''}`}
            onClick={() => {
              if (tab.available) {
                setShowSplit(false)
                setViewMode(tab.id)
              }
            }}
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
          {/* Floating Indicators for Split View */}
          <div style={{
            position: 'absolute', top: 12, left: 16, zIndex: 10,
            background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)',
            color: 'var(--text-secondary)', padding: '4px 10px', borderRadius: 6,
            fontSize: 11, fontWeight: 600, pointerEvents: 'none',
            border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#94a3b8' }} />
            Original
          </div>
          <div style={{
            position: 'absolute', top: 12, right: 16, zIndex: 10,
            background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)',
            color: 'var(--accent-primary)', padding: '4px 10px', borderRadius: 6,
            fontSize: 11, fontWeight: 600, pointerEvents: 'none',
            border: '1px solid var(--border-accent)', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-primary)' }} />
            Vector Output
          </div>

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
              width:22, height:22, borderRadius:'50%',
              background:'var(--accent-primary)',
              border:'2px solid white',
              display:'flex', alignItems:'center', justifyContent:'center',
              fontSize:11, color:'white', userSelect:'none',
              boxShadow:'0 2px 8px rgba(0,0,0,0.5)',
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
