import React, { useCallback } from 'react'
import { useAppStore } from '../store/appStore'
import { uploadImage, analyzeImage } from '../api/client'

export default function DropZone() {
  const { stage, setStage, setImageInfo, setAnalysisResult, reset } = useAppStore()
  const [dragOver, setDragOver] = React.useState(false)

  const processFile = useCallback(async (file: File) => {
    if (!file.type.startsWith('image/') && !file.name.match(/\.(png|jpg|jpeg|bmp|webp)$/i)) {
      setStage('error', 'Unsupported file type. Please upload PNG, JPG, BMP, or WebP.')
      return
    }
    reset()
    setStage('uploading')
    try {
      const info = await uploadImage(file)
      setImageInfo(info)
      setStage('analyzing')
      const analysis = await analyzeImage(info.session_id)
      setAnalysisResult(analysis)
      setStage('idle')
    } catch (err: any) {
      setStage('error', err?.response?.data?.detail || `Upload failed: ${String(err)}`)
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
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = '.png,.jpg,.jpeg,.bmp,.webp,image/png,image/jpeg,image/bmp,image/webp'
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (file) processFile(file)
    }
    input.click()
  }

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const items = e.clipboardData.items
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.startsWith('image/')) {
        const file = items[i].getAsFile()
        if (file) processFile(file)
        break
      }
    }
  }, [processFile])

  const isLoading = stage === 'uploading' || stage === 'analyzing'

  return (
    <div
      className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={handleClick}
      onPaste={handlePaste}
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
          {isLoading ? 'Processing…' : 'Drop image here'}
        </div>
        <div className="upload-subtitle" style={{marginTop: 4}}>
          {isLoading
            ? stage === 'uploading' ? 'Uploading your image…' : 'Analyzing image type…'
            : 'or click to browse · paste from clipboard supported'}
        </div>
      </div>

      <div className="upload-formats">
        {['PNG', 'JPG', 'JPEG', 'BMP', 'WebP'].map(f => (
          <span key={f} className="format-badge">{f}</span>
        ))}
      </div>

      <div style={{fontSize: 11, color: 'var(--text-muted)'}}>
        Max 50 MB · Up to 8000×8000 px
      </div>
    </div>
  )
}

