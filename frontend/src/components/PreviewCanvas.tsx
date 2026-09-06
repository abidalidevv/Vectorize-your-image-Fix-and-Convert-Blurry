import React, { useRef, useState, useEffect } from 'react'
import { useAppStore } from '../store/appStore'
import type { ViewMode } from '../store/appStore'

export default function PreviewCanvas() {
  const {
    imageInfo, vectorResult, preprocessedUrl, quantizedUrl,
    enhancedResult, bgRemovedResult, eraserResult, activeTool,
    eraserSettings, setEraserMaskData,
    viewMode, setViewMode, zoom, setZoom,
  } = useAppStore()

  const containerRef = useRef<HTMLDivElement>(null)
  const maskCanvasRef = useRef<HTMLCanvasElement>(null)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const [lastMouse, setLastMouse] = useState({ x: 0, y: 0 })
  const [splitPos, setSplitPos] = useState(50)
  const [draggingSplit, setDraggingSplit] = useState(false)
  const [showSplit, setShowSplit] = useState(false)

  // Eraser drawing state
  const [isDrawing, setIsDrawing] = useState(false)
  const [brushPos, setBrushPos] = useState<{ x: number; y: number } | null>(null)
  const strokeHistoryRef = useRef<ImageData[]>([])
  const [spacePressed, setSpacePressed] = useState(false)

  // Reset pan when image changes
  useEffect(() => {
    setPan({ x: 0, y: 0 })
    setZoom(1)
    if (maskCanvasRef.current) {
      const ctx = maskCanvasRef.current.getContext('2d')
      if (ctx) ctx.clearRect(0, 0, maskCanvasRef.current.width, maskCanvasRef.current.height)
    }
    strokeHistoryRef.current = []
    setEraserMaskData(null)
  }, [imageInfo?.session_id, setEraserMaskData, setZoom])

  // Track spacebar for panning in eraser mode
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space' && !spacePressed) {
        setSpacePressed(true)
      }
    }
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setSpacePressed(false)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
    }
  }, [spacePressed])

  // Listen for clear mask and undo mask custom events
  useEffect(() => {
    const handleClear = () => {
      const canvas = maskCanvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height)
      strokeHistoryRef.current = []
      setEraserMaskData(null)
    }

    const handleUndo = () => {
      const canvas = maskCanvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      const history = strokeHistoryRef.current
      if (history.length > 0) {
        history.pop()
        if (history.length > 0) {
          ctx.putImageData(history[history.length - 1], 0, 0)
        } else {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
        }
        updateMaskData()
      }
    }

    window.addEventListener('vectorforge:clear_eraser_mask', handleClear)
    window.addEventListener('vectorforge:undo_eraser_mask', handleUndo)
    return () => {
      window.removeEventListener('vectorforge:clear_eraser_mask', handleClear)
      window.removeEventListener('vectorforge:undo_eraser_mask', handleUndo)
    }
  }, [setEraserMaskData])

  // Non-passive wheel event listener to prevent browser page zoom
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const handleCanvasWheel = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()

      const rect = el.getBoundingClientRect()
      const mouseX = e.clientX - rect.left - rect.width / 2
      const mouseY = e.clientY - rect.top - rect.height / 2

      const factor = e.deltaY < 0 ? 1.18 : 0.85

      setZoom((prevZoom: number) => {
        const nextZoom = Math.min(20, Math.max(0.05, prevZoom * factor))
        setPan(prevPan => ({
          x: mouseX - (mouseX - prevPan.x) * (nextZoom / prevZoom),
          y: mouseY - (mouseY - prevPan.y) * (nextZoom / prevZoom),
        }))
        return nextZoom
      })
    }

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

  // Determine current active processed URL and target labels
  const processedInfo = (() => {
    if (activeTool === 'enhancer') {
      return {
        url: enhancedResult?.url ?? null,
        label: 'Enhanced HD',
        available: !!enhancedResult,
        width: enhancedResult?.width ?? imageInfo?.width,
        height: enhancedResult?.height ?? imageInfo?.height,
        isVector: false,
      }
    }
    if (activeTool === 'bgremover') {
      return {
        url: bgRemovedResult?.url ?? null,
        label: 'Cutout / Removed BG',
        available: !!bgRemovedResult,
        width: bgRemovedResult?.width ?? imageInfo?.width,
        height: bgRemovedResult?.height ?? imageInfo?.height,
        isVector: false,
      }
    }
    if (activeTool === 'eraser') {
      return {
        url: eraserResult?.url ?? null,
        label: 'Inpainted PNG',
        available: !!eraserResult,
        width: eraserResult?.width ?? imageInfo?.width,
        height: eraserResult?.height ?? imageInfo?.height,
        isVector: false,
      }
    }
    // Vectorizer
    return {
      url: vectorResult?.svg_url ?? (quantizedUrl || preprocessedUrl || null),
      label: 'Vector Output',
      available: !!vectorResult,
      width: imageInfo?.width,
      height: imageInfo?.height,
      isVector: viewMode === 'vector' && !!vectorResult,
    }
  })()

  // Determine URL to show in single preview mode
  const currentUrl = (() => {
    if (activeTool === 'enhancer') {
      if (viewMode === 'original') return imageInfo?.preview_url ?? null
      if (enhancedResult) return enhancedResult.url
      return imageInfo?.preview_url ?? null
    }
    if (activeTool === 'bgremover') {
      if (viewMode === 'original') return imageInfo?.preview_url ?? null
      if (bgRemovedResult) return bgRemovedResult.url
      return imageInfo?.preview_url ?? null
    }
    if (activeTool === 'eraser') {
      if (viewMode === 'original') return imageInfo?.preview_url ?? null
      if (eraserResult) return eraserResult.url
      return imageInfo?.preview_url ?? null
    }
    // Vectorizer
    if (viewMode === 'vector' && vectorResult) return vectorResult.svg_url
    if (viewMode === 'enhanced') {
      if (quantizedUrl) return quantizedUrl
      if (preprocessedUrl) return preprocessedUrl
    }
    return imageInfo?.preview_url ?? null
  })()

  // Update binary mask export for backend
  const updateMaskData = () => {
    const canvas = maskCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const off = document.createElement('canvas')
    off.width = canvas.width
    off.height = canvas.height
    const offCtx = off.getContext('2d')
    if (!offCtx) {
      setEraserMaskData(canvas.toDataURL('image/png'))
      return
    }
    offCtx.drawImage(canvas, 0, 0)
    const imgData = offCtx.getImageData(0, 0, off.width, off.height)
    const d = imgData.data
    let hasDrawn = false
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] > 10) {
        d[i] = 255
        d[i + 1] = 255
        d[i + 2] = 255
        d[i + 3] = 255
        hasDrawn = true
      } else {
        d[i] = 0
        d[i + 1] = 0
        d[i + 2] = 0
        d[i + 3] = 0
      }
    }
    if (hasDrawn) {
      offCtx.putImageData(imgData, 0, 0)
      setEraserMaskData(off.toDataURL('image/png'))
    } else {
      setEraserMaskData(null)
    }
  }

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = maskCanvasRef.current
    if (!canvas) return { x: 0, y: 0 }
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    }
  }

  const handleBrushDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (e.button !== 0 || spacePressed) {
      handleMouseDown(e)
      return
    }
    const canvas = maskCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    strokeHistoryRef.current.push(ctx.getImageData(0, 0, canvas.width, canvas.height))
    if (strokeHistoryRef.current.length > 25) strokeHistoryRef.current.shift()

    setIsDrawing(true)
    const { x, y } = getCanvasCoords(e)

    ctx.strokeStyle = 'rgba(244, 63, 94, 0.65)'
    ctx.fillStyle = 'rgba(244, 63, 94, 0.65)'
    ctx.lineWidth = eraserSettings.brushSize
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    ctx.beginPath()
    ctx.arc(x, y, eraserSettings.brushSize / 2, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.moveTo(x, y)
  }

  const handleBrushMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setBrushPos({ x: e.clientX, y: e.clientY })
    if (spacePressed && dragging) {
      handleMouseMove(e)
      return
    }
    if (!isDrawing) return
    const canvas = maskCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { x, y } = getCanvasCoords(e)
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const handleBrushUp = () => {
    if (isDrawing) {
      setIsDrawing(false)
      const canvas = maskCanvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        if (ctx) ctx.closePath()
      }
      updateMaskData()
    }
    if (dragging) {
      handleMouseUp()
    }
  }

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0 && e.button !== 1 && e.button !== 2) return
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

  // View Mode Tabs adapted per tool
  const viewTabs: { id: ViewMode; label: string; available: boolean }[] = (() => {
    if (activeTool === 'enhancer') {
      return [
        { id: 'original', label: 'Original', available: true },
        { id: 'enhanced', label: 'Enhanced HD', available: !!enhancedResult },
      ]
    }
    if (activeTool === 'bgremover') {
      return [
        { id: 'original', label: 'Original', available: true },
        { id: 'enhanced', label: 'Cutout PNG', available: !!bgRemovedResult },
      ]
    }
    if (activeTool === 'eraser') {
      return [
        { id: 'original', label: 'Original & Brush', available: true },
        { id: 'enhanced', label: 'Clean Result', available: !!eraserResult },
      ]
    }
    return [
      { id: 'original', label: 'Original', available: true },
      { id: 'enhanced', label: 'Enhanced', available: !!(preprocessedUrl || quantizedUrl) },
      { id: 'vector',   label: 'Vector',   available: !!vectorResult },
    ]
  })()

  const transformStyle: React.CSSProperties = {
    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
    transformOrigin: 'center center',
    transition: dragging ? 'none' : 'transform 0.05s ease',
  }

  const canSplit = processedInfo.available && !!processedInfo.url

  const displayWidth = (() => {
    if (activeTool === 'enhancer' && viewMode === 'enhanced' && enhancedResult) return enhancedResult.width
    if (activeTool === 'eraser' && viewMode === 'enhanced' && eraserResult) return eraserResult.width
    if (activeTool === 'bgremover' && viewMode === 'enhanced' && bgRemovedResult) return bgRemovedResult.width
    return imageInfo.width
  })()

  const displayHeight = (() => {
    if (activeTool === 'enhancer' && viewMode === 'enhanced' && enhancedResult) return enhancedResult.height
    if (activeTool === 'eraser' && viewMode === 'enhanced' && eraserResult) return eraserResult.height
    if (activeTool === 'bgremover' && viewMode === 'enhanced' && bgRemovedResult) return bgRemovedResult.height
    return imageInfo.height
  })()

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
      {/* View Mode Toolbar */}
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

        {canSplit && (
          <>
            <div style={{ width: 1, height: 16, background: 'var(--border-default)', margin: '0 4px' }} />
            <button
              className={`view-tab ${showSplit ? 'active' : ''}`}
              onClick={() => setShowSplit(!showSplit)}
              title="Toggle split before/after comparison"
            >
              ⇔ Split View
            </button>
          </>
        )}
      </div>

      {/* Main Preview (Single or Split) */}
      {!showSplit ? (
        <div
          className="preview-viewport"
          style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <div style={transformStyle}>
            {processedInfo.isVector ? (
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
              <div style={{ position: 'relative', display: 'inline-block', width: displayWidth, height: displayHeight }}>
                <img
                  src={currentUrl!}
                  alt="Preview"
                  style={{
                    display: 'block',
                    maxWidth: 'none',
                    width: displayWidth,
                    height: displayHeight,
                    imageRendering: zoom >= 4 ? 'pixelated' : 'auto',
                  }}
                  draggable={false}
                />
                {/* Interactive Mask Brush Overlay for Magic Eraser */}
                {activeTool === 'eraser' && (viewMode === 'original' || !eraserResult) && (
                  <canvas
                    ref={maskCanvasRef}
                    width={imageInfo.width}
                    height={imageInfo.height}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      cursor: spacePressed ? 'grab' : 'crosshair',
                      zIndex: 10,
                      touchAction: 'none',
                    }}
                    onMouseDown={handleBrushDown}
                    onMouseMove={handleBrushMove}
                    onMouseUp={handleBrushUp}
                    onMouseLeave={() => { setBrushPos(null); handleBrushUp() }}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Split View */
        <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
          {/* Floating Indicators */}
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
            {processedInfo.label}
          </div>

          {/* Left side: Original */}
          <div
            style={{
              position: 'absolute', inset: 0, overflow: 'hidden',
              clipPath: `inset(0 ${100 - splitPos}% 0 0)`,
            }}
          >
            <div style={{ ...transformStyle, width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src={imageInfo.preview_url}
                alt="Original"
                style={{ maxWidth: 'none', width: imageInfo.width, height: imageInfo.height }}
                draggable={false}
              />
            </div>
          </div>

          {/* Right side: Processed */}
          <div
            style={{
              position: 'absolute', inset: 0, overflow: 'hidden',
              clipPath: `inset(0 0 0 ${splitPos}%)`,
            }}
          >
            <div style={{ ...transformStyle, width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <img
                src={processedInfo.url!}
                alt="Processed"
                style={{ maxWidth: 'none', width: imageInfo.width, height: imageInfo.height }}
                draggable={false}
              />
            </div>
          </div>

          {/* Split Handle */}
          <div
            style={{
              position: 'absolute', top: 0, bottom: 0,
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
              position: 'absolute', top: '50%', left: '50%',
              transform: 'translate(-50%,-50%)',
              width: 22, height: 22, borderRadius: '50%',
              background: 'var(--accent-primary)',
              border: '2px solid white',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, color: 'white', userSelect: 'none',
              boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
            }}>⇔</div>
          </div>
        </div>
      )}

      {/* Floating Circular Brush Cursor for Eraser */}
      {activeTool === 'eraser' && brushPos && !spacePressed && (
        <div
          style={{
            position: 'fixed',
            left: brushPos.x,
            top: brushPos.y,
            width: eraserSettings.brushSize * zoom,
            height: eraserSettings.brushSize * zoom,
            borderRadius: '50%',
            border: '1.5px solid rgba(244, 63, 94, 0.95)',
            background: 'rgba(244, 63, 94, 0.2)',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'none',
            zIndex: 9999,
          }}
        />
      )}

      {/* Zoom Controls */}
      <div className="zoom-controls">
        <div className="zoom-group">
          <button className="zoom-btn" onClick={zoomIn} title="Zoom in">+</button>
          <div className="zoom-display">{zoomPct}</div>
          <button className="zoom-btn" onClick={zoomOut} title="Zoom out">−</button>
        </div>
        <div className="zoom-group" style={{ marginTop: 4 }}>
          {[['Fit', 1.0], ['1×', 1.0], ['2×', 2.0], ['5×', 5.0], ['10×', 10.0], ['20×', 20.0]].map(([label, val]) => (
            <button
              key={String(label)}
              className="zoom-btn"
              style={{ fontSize: 9, height: 22 }}
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

      {/* Badges */}
      {activeTool === 'vectorizer' && vectorResult && (
        <div style={{
          position: 'absolute', bottom: 'var(--space-3)', left: 'var(--space-3)',
          background: 'var(--success-bg)', border: '1px solid rgba(52,211,153,0.3)',
          color: 'var(--success)', padding: '3px 10px', borderRadius: 'var(--radius-md)',
          fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4,
          pointerEvents: 'none',
        }}>
          ◈ True Vector — {vectorResult?.stats.path_count} paths
        </div>
      )}

      {activeTool === 'enhancer' && enhancedResult && (
        <div style={{
          position: 'absolute', bottom: 'var(--space-3)', left: 'var(--space-3)',
          background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)',
          color: '#10b981', padding: '3px 10px', borderRadius: 'var(--radius-md)',
          fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4,
          pointerEvents: 'none',
        }}>
          ✨ Enhanced HD — {enhancedResult.width}×{enhancedResult.height}px
        </div>
      )}

      {activeTool === 'bgremover' && bgRemovedResult && (
        <div style={{
          position: 'absolute', bottom: 'var(--space-3)', left: 'var(--space-3)',
          background: 'rgba(245,158,11,0.15)', border: '1px solid rgba(245,158,11,0.3)',
          color: '#f59e0b', padding: '3px 10px', borderRadius: 'var(--radius-md)',
          fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4,
          pointerEvents: 'none',
        }}>
          ✂️ Cutout Ready — Transparent PNG
        </div>
      )}

      {activeTool === 'eraser' && eraserResult && (
        <div style={{
          position: 'absolute', bottom: 'var(--space-3)', left: 'var(--space-3)',
          background: 'rgba(244,63,94,0.15)', border: '1px solid rgba(244,63,94,0.3)',
          color: '#f43f5e', padding: '3px 10px', borderRadius: 'var(--radius-md)',
          fontSize: 11, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 4,
          pointerEvents: 'none',
        }}>
          🪄 Object Erased — Clean Inpainted Result
        </div>
      )}
    </div>
  )
}
