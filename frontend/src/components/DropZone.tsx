import React, { useCallback, useRef } from 'react'
import { useAppStore } from '../store/appStore'
import { uploadImage, analyzeImage } from '../api/client'

export default function DropZone() {
  const { stage, setStage, setImageInfo, setAnalysisResult, reset } = useAppStore()
  const [dragOver, setDragOver] = React.useState(false)
  const isUploadingRef = useRef(false)

  const processFile = useCallback(async (file: File) => {
    if (isUploadingRef.current) return
    if (!file.type.startsWith('image/') && !file.name.match(/\.(png|jpg|jpeg|bmp|webp)$/i)) {
      setStage('error', 'Unsupported file type. Please upload PNG, JPG, BMP, or WebP.')
      return
    }

    isUploadingRef.current = true
    reset()
    setStage('uploading')

    try {
      const info = await uploadImage(file)
      setImageInfo(info)
      setStage('idle')

      // Analyze in background without blocking UI
      try {
        const analysis = await analyzeImage(info.session_id)
        setAnalysisResult(analysis)
      } catch (analysisErr) {
        console.warn('Auto analysis note:', analysisErr)
      }
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || `Upload failed: ${String(err)}`)
    } finally {
      isUploadingRef.current = false
    }
  }, [reset, setStage, setImageInfo, setAnalysisResult])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) processFile(file)
  }, [processFile])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => setDragOver(false)

  const handleClick = () => {
    if (isUploadingRef.current) return
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.png,.jpg,.jpeg,.bmp,.webp,image/png,image/jpeg,image/bmp,image/webp'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) processFile(file)
    }
    input.click()
  }

  const isLoading = stage === 'uploading'

  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      role="button"
      aria-label="Upload image"
    >
      <div className="upload-icon">
        {isLoading ? <span className="spinner" /> : '🎨'}
      </div>

      <div>
        <div className="upload-title">
          {isLoading ? 'Uploading…' : 'Drop image here'}
        </div>
        <div className="upload-subtitle" style={{marginTop: 4}}>
          {isLoading
            ? 'Uploading your image…'
            : 'or click to browse · paste from clipboard supported'}
        </div>
      </div>

      <div className="upload-formats">
        {['PNG', 'JPG', 'JPEG', 'BMP', 'WebP'].map(f => (
          <span key={f} className="format-badge">{f}</span>
        ))}
      </div>

      <div style={{fontSize: 11, color: 'var(--text-muted)'}}>
        Maximum file size: 50 MB · All processing runs locally
      </div>
    </div>
  )
}
