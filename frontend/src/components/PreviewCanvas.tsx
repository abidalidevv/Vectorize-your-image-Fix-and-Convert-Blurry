import React, { useRef, useState, useEffect } from 'react'
import { useAppStore } from '../store/appStore'
import type { ViewMode } from '../store/appStore'

// Module-level Spacebar physical state tracking fallback
let isSpaceGloballyDown = false

const isSpaceKey = (e: KeyboardEvent) =>
  e.code === 'Space' || e.key === ' ' || e.key === 'Spacebar' || e.keyCode === 32 || e.which === 32

const isTextInput = (target: EventTarget | null) => {
  if (!target || !(target instanceof HTMLElement)) return false
  const tag = target.tagName
  if (tag === 'TEXTAREA') return true
  if (tag === 'INPUT') {
    const type = (target as HTMLInputElement).type
    return !['range', 'checkbox', 'radio', 'button', 'submit', 'color', 'reset'].includes(type)
  }
  return target.isContentEditable
}

export default function PreviewCanvas() {
  const {
    imageInfo, vectorResult, preprocessedUrl, quantizedUrl,
    enhancedResult, bgRemovedResult, eraserResult, activeTool,
    eraserSettings, setEraserMaskData,
    eraserToolMode,
    viewMode, setViewMode, zoom, setZoom,
  } = useAppStore()

  const containerRef = useRef<HTMLDivElement>(null)
  const maskCanvasRef = useRef<HTMLCanvasElement>(null)
  const viewportRef = useRef<HTMLDivElement>(null)

  // Smooth Pan State & Ref
  const [pan, _setPan] = useState({ x: 0, y: 0 })
  const panRef = useRef({ x: 0, y: 0 })
  const zoomRef = useRef(zoom)
  useEffect(() => {
    zoomRef.current = zoom
  }, [zoom])

  const setPan = (updater: { x: number; y: number } | ((p: { x: number; y: number }) => { x: number; y: number })) => {
    _setPan(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      panRef.current = next
      if (viewportRef.current) {
        viewportRef.current.style.transform = `translate(${next.x}px, ${next.y}px) scale(${zoomRef.current})`
      }
      return next
    })
  }

  // Pan drag state
  const isDraggingRef = useRef(false)
  const [dragging, setDragging] = useState(false)
  const dragOriginRef = useRef({ mouseX: 0, mouseY: 0, panX: 0, panY: 0 })

  // Split View Drag State
  const draggingSplitRef = useRef(false)
  const [draggingSplit, setDraggingSplit] = useState(false)
  const [splitPos, setSplitPos] = useState(50)
  const [showSplit, setShowSplit] = useState(false)

  // Eraser drawing state
  const isDrawingRef = useRef(false)
  const [isDrawing, setIsDrawing] = useState(false)
  const [brushPos, setBrushPos] = useState<{ x: number; y: number } | null>(null)
  const strokeHistoryRef = useRef<ImageData[]>([])

  // Spacebar tracking
  const spacePressedRef = useRef(isSpaceGloballyDown)
  const [spacePressed, setSpacePressed] = useState(isSpaceGloballyDown)

  // Robust window-level keyboard listeners
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isSpaceKey(e)) return
      if (isTextInput(e.target)) return

      // Prevent page scroll and button click
      e.preventDefault()

      isSpaceGloballyDown = true
      if (!spacePressedRef.current) {
        spacePressedRef.current = true
        setSpacePressed(true)
        setBrushPos(null)
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      if (!isSpaceKey(e)) return
      if (isTextInput(e.target)) return

      e.preventDefault()
      isSpaceGloballyDown = false
      spacePressedRef.current = false
      setSpacePressed(false)
    }

    const handleBlur = () => {
      isSpaceGloballyDown = false
      spacePressedRef.current = false
      setSpacePressed(false)
    }

    const handleVisibility = () => {
      if (document.visibilityState === 'hidden') {
        isSpaceGloballyDown = false
        spacePressedRef.current = false
        setSpacePressed(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown, { capture: true, passive: false })
    window.addEventListener('keyup', handleKeyUp, { capture: true, passive: false })
    window.addEventListener('blur', handleBlur)
    document.addEventListener('visibilitychange', handleVisibility)

    return () => {
      window.removeEventListener('keydown', handleKeyDown, { capture: true })
      window.removeEventListener('keyup', handleKeyUp, { capture: true })
      window.removeEventListener('blur', handleBlur)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [])

  // Helper to check whether a mouse button should initiate canvas panning
  const canPanWithButton = (button: number, e?: React.MouseEvent | MouseEvent) => {
    // Middle click (wheel) or Right click always pans in all modes
    if (button === 1 || button === 2) return true
    // Left click (button 0):
    if (button === 0) {
      // If Spacebar is actively held down OR Alt key is held down -> ALWAYS PAN
      if (spacePressedRef.current || spacePressed || isSpaceGloballyDown || e?.altKey) return true
      // In non-eraser tools (Vectorizer, Enhancer, BgRemover) -> Always Pan
      if (activeTool !== 'eraser') return true
      // In Magic Eraser, if user is viewing the clean result (viewMode === 'enhanced') -> Pan
      if (viewMode === 'enhanced') return true
      // In Magic Eraser, if user explicitly toggled Pan mode -> Pan
      if (eraserToolMode === 'pan') return true
      // Otherwise (Magic Eraser in brush mode on original image) -> Never Pan on left click!
      return false
    }
    return false
  }

  // Active pan mode state for cursor display
  const isPanMode = canPanWithButton(0)

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

  // Global window mousemove & mouseup listeners for seamless 1:1 dragging
  useEffect(() => {
    const onWindowMouseMove = (e: MouseEvent) => {
      // If Space is held (or Alt) while left mouse button is down, dynamically initiate panning
      const isSpace = spacePressedRef.current || isSpaceGloballyDown || e.altKey
      if (isSpace && (e.buttons === 1 || e.buttons === 4) && !isDraggingRef.current) {
        if (isDrawingRef.current) {
          isDrawingRef.current = false
          setIsDrawing(false)
          const canvas = maskCanvasRef.current
          if (canvas && strokeHistoryRef.current.length > 0) {
            const ctx = canvas.getContext('2d')
            if (ctx) {
              const last = strokeHistoryRef.current.pop()
              if (last) ctx.putImageData(last, 0, 0)
            }
          }
          updateMaskData()
        }
        isDraggingRef.current = true
        setDragging(true)
        dragOriginRef.current = {
          mouseX: e.clientX,
          mouseY: e.clientY,
          panX: panRef.current.x,
          panY: panRef.current.y,
        }
      }

      // 1. Panning canvas
      if (isDraggingRef.current) {
        if (e.buttons === 0) {
          isDraggingRef.current = false
          setDragging(false)
          return
        }
        const dx = e.clientX - dragOriginRef.current.mouseX
        const dy = e.clientY - dragOriginRef.current.mouseY
        const nextPan = {
          x: dragOriginRef.current.panX + dx,
          y: dragOriginRef.current.panY + dy,
        }
        panRef.current = nextPan
        if (viewportRef.current) {
          viewportRef.current.style.transform = `translate(${nextPan.x}px, ${nextPan.y}px) scale(${zoomRef.current})`
        }
        _setPan(nextPan)
        return
      }

      // 2. Continuous mask drawing if pointer moved outside canvas during stroke
      if (isDrawingRef.current && maskCanvasRef.current && e.target !== maskCanvasRef.current) {
        const canvas = maskCanvasRef.current
        const ctx = canvas.getContext('2d')
        if (ctx) {
          const { x, y } = getCanvasCoords(e)
          ctx.lineTo(x, y)
          ctx.stroke()
        }
        return
      }

      // 3. Split view handle dragging
      if (draggingSplitRef.current && containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        const pos = ((e.clientX - rect.left) / rect.width) * 100
        setSplitPos(Math.max(5, Math.min(95, pos)))
      }
    }

    const onWindowMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false
        setDragging(false)
      }
      if (draggingSplitRef.current) {
        draggingSplitRef.current = false
        setDraggingSplit(false)
      }
      if (isDrawingRef.current) {
        isDrawingRef.current = false
        setIsDrawing(false)
        const canvas = maskCanvasRef.current
        if (canvas) {
          const ctx = canvas.getContext('2d')
          if (ctx) ctx.closePath()
        }
        updateMaskData()
      }
    }

    window.addEventListener('mousemove', onWindowMouseMove)
    window.addEventListener('mouseup', onWindowMouseUp)
    return () => {
      window.removeEventListener('mousemove', onWindowMouseMove)
      window.removeEventListener('mouseup', onWindowMouseUp)
    }
  }, [])

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
        const nextPan = {
          x: mouseX - (mouseX - panRef.current.x) * (nextZoom / prevZoom),
          y: mouseY - (mouseY - panRef.current.y) * (nextZoom / prevZoom),
        }
        panRef.current = nextPan
        _setPan(nextPan)
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

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement> | MouseEvent) => {
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

  // Unified Pan initiation (Middle-click, Right-click, Space+drag, Pan mode)
  const startPan = (clientX: number, clientY: number, button: number, e?: React.MouseEvent | MouseEvent) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }

    if (isDrawingRef.current) {
      isDrawingRef.current = false
      setIsDrawing(false)
      const canvas = maskCanvasRef.current
      if (canvas && strokeHistoryRef.current.length > 0) {
        const ctx = canvas.getContext('2d')
        if (ctx) {
          const last = strokeHistoryRef.current.pop()
          if (last) ctx.putImageData(last, 0, 0)
        }
      }
      updateMaskData()
    }

    isDraggingRef.current = true
    setDragging(true)
    dragOriginRef.current = {
      mouseX: clientX,
      mouseY: clientY,
      panX: panRef.current.x,
      panY: panRef.current.y,
    }
  }

  // Canvas-specific handlers for Magic Eraser mask drawing & panning
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const isSpace = spacePressedRef.current || spacePressed || isSpaceGloballyDown || e.altKey

    // If Space is pressed, or Middle/Right click, or user switched to pan mode -> PAN IMMEDIATELY
    if (isSpace || canPanWithButton(e.button, e)) {
      startPan(e.clientX, e.clientY, e.button, e)
      return
    }

    // Left click in brush mode without Space -> DRAW MASK ONLY (NEVER PAN)
    if (e.button !== 0) return
    e.preventDefault()
    e.stopPropagation()

    const canvas = maskCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    strokeHistoryRef.current.push(ctx.getImageData(0, 0, canvas.width, canvas.height))
    if (strokeHistoryRef.current.length > 25) strokeHistoryRef.current.shift()

    isDrawingRef.current = true
    setIsDrawing(true)
    const { x, y } = getCanvasCoords(e)

    ctx.strokeStyle = 'rgba(244, 63, 94, 0.7)'
    ctx.fillStyle = 'rgba(244, 63, 94, 0.7)'
    ctx.lineWidth = eraserSettings.brushSize
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'

    ctx.beginPath()
    ctx.arc(x, y, eraserSettings.brushSize / 2, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.moveTo(x, y)
  }

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const isSpace = spacePressedRef.current || spacePressed || isSpaceGloballyDown || e.altKey
    const isPan = isSpace || canPanWithButton(0, e)

    // In pan mode or space held: never draw, hide brush cursor ring
    if (isPan) {
      if (brushPos !== null) setBrushPos(null)

      // If user holds Space and left mouse button is down, ensure dragging starts
      if (e.buttons === 1 && !isDraggingRef.current) {
        startPan(e.clientX, e.clientY, 0, e)
      }

      // If currently dragging, update pan directly right here for 144fps responsiveness
      if (isDraggingRef.current) {
        const dx = e.clientX - dragOriginRef.current.mouseX
        const dy = e.clientY - dragOriginRef.current.mouseY
        const nextPan = {
          x: dragOriginRef.current.panX + dx,
          y: dragOriginRef.current.panY + dy,
        }
        panRef.current = nextPan
        if (viewportRef.current) {
          viewportRef.current.style.transform = `translate(${nextPan.x}px, ${nextPan.y}px) scale(${zoomRef.current})`
        }
        _setPan(nextPan)
        return
      }
      return
    }

    // Brush mode: track cursor for circular overlay
    setBrushPos({ x: e.clientX, y: e.clientY })

    if (!isDrawingRef.current) return
    e.preventDefault()
    e.stopPropagation()

    const canvas = maskCanvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const { x, y } = getCanvasCoords(e)
    ctx.lineTo(x, y)
    ctx.stroke()
  }

  const handleCanvasMouseUp = () => {
    if (isDraggingRef.current) {
      isDraggingRef.current = false
      setDragging(false)
    }
    if (isDrawingRef.current) {
      isDrawingRef.current = false
      setIsDrawing(false)
      const canvas = maskCanvasRef.current
      if (canvas) {
        const ctx = canvas.getContext('2d')
        if (ctx) ctx.closePath()
      }
      updateMaskData()
    }
  }

  const handleCanvasMouseLeave = () => {
    setBrushPos(null)
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
      tabIndex={0}
      onMouseDown={(e) => {
        if (canPanWithButton(e.button, e)) {
          startPan(e.clientX, e.clientY, e.button, e)
        }
      }}
      onContextMenu={(e) => e.preventDefault()}
      style={{
        position: 'relative',
        flex: 1,
        minHeight: 0,
        overflow: 'hidden',
        touchAction: 'none',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        outline: 'none',
        cursor: isPanMode ? (dragging ? 'grabbing' : 'grab') : (activeTool === 'eraser' ? 'crosshair' : 'grab'),
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
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            userSelect: 'none',
            WebkitUserSelect: 'none',
          }}
        >
          <div ref={viewportRef} style={transformStyle}>
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
                  pointerEvents: 'none',
                  userSelect: 'none',
                }}
                draggable={false}
              />
            ) : (
              <div style={{ position: 'relative', display: 'inline-block', width: displayWidth, height: displayHeight, userSelect: 'none' }}>
                <img
                  src={currentUrl!}
                  alt="Preview"
                  style={{
                    display: 'block',
                    maxWidth: 'none',
                    width: displayWidth,
                    height: displayHeight,
                    imageRendering: zoom >= 4 ? 'pixelated' : 'auto',
                    pointerEvents: 'none',
                    userSelect: 'none',
                  }}
                  draggable={false}
                />
                {/* Interactive Mask Brush Overlay for Magic Eraser */}
                {activeTool === 'eraser' && (viewMode === 'original' || !eraserResult) && (
                  <canvas
                    ref={maskCanvasRef}
                    width={imageInfo.width}
                    height={imageInfo.height}
                    draggable={false}
                    onDragStart={(e) => e.preventDefault()}
                    style={{
                      position: 'absolute',
                      inset: 0,
                      width: '100%',
                      height: '100%',
                      cursor: isPanMode ? (dragging ? 'grabbing' : 'grab') : 'crosshair',
                      zIndex: 10,
                      touchAction: 'none',
                      userSelect: 'none',
                    }}
                    onMouseDown={handleCanvasMouseDown}
                    onMouseMove={handleCanvasMouseMove}
                    onMouseUp={handleCanvasMouseUp}
                    onMouseLeave={handleCanvasMouseLeave}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Split View */
        <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', userSelect: 'none' }}>
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
                style={{ maxWidth: 'none', width: imageInfo.width, height: imageInfo.height, pointerEvents: 'none', userSelect: 'none' }}
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
                style={{ maxWidth: 'none', width: imageInfo.width, height: imageInfo.height, pointerEvents: 'none', userSelect: 'none' }}
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
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              draggingSplitRef.current = true
              setDraggingSplit(true)
            }}
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
      {activeTool === 'eraser' && viewMode === 'original' && brushPos && !isPanMode && (
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
