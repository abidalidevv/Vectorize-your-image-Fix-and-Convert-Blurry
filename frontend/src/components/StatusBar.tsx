import React from 'react'
import { useAppStore } from '../store/appStore'

const STAGE_LABELS: Record<string, string> = {
  idle: 'Ready',
  uploading: 'Uploading…',
  analyzing: 'Analyzing…',
  preprocessing: 'Preprocessing…',
  quantizing: 'Quantizing colors…',
  vectorizing: 'Vectorizing…',
  exporting: 'Exporting…',
  error: 'Error',
}

export default function StatusBar() {
  const { imageInfo, vectorResult, stage, zoom, errorMessage } = useAppStore()

  const isWorking = ['uploading','analyzing','preprocessing','quantizing','vectorizing','exporting'].includes(stage)

  const formatBytes = (b: number) => {
    if (b > 1024 * 1024) return `${(b / 1024 / 1024).toFixed(2)} MB`
    if (b > 1024) return `${(b / 1024).toFixed(1)} KB`
    return `${b} B`
  }

  return (
    <div className="statusbar">
      {imageInfo && (
        <>
          <div className="statusbar-item statusbar-optional">
            <span>Dimensions</span>
            <span className="value">{imageInfo.width} × {imageInfo.height} px</span>
          </div>
          <div className="statusbar-sep statusbar-optional" />
          <div className="statusbar-item statusbar-optional">
            <span>Format</span>
            <span className="value">{imageInfo.format}</span>
          </div>
          <div className="statusbar-sep statusbar-optional" />
        </>
      )}

      <div className="statusbar-item">
        <span>Zoom</span>
        <span className="value">{Math.round(zoom * 100)}%</span>
      </div>

      {vectorResult && (
        <>
          <div className="statusbar-sep" />
          <div className="statusbar-item">
            <span>Paths</span>
            <span className="value">{vectorResult.stats.path_count}</span>
          </div>
          <div className="statusbar-sep statusbar-optional" />
          <div className="statusbar-item statusbar-optional">
            <span>SVG Size</span>
            <span className="value">{formatBytes(vectorResult.stats.file_size_bytes)}</span>
          </div>
          <div className="statusbar-sep statusbar-optional" />
          <div className="statusbar-item statusbar-optional">
            <span>Colors</span>
            <span className="value">{vectorResult.stats.color_count}</span>
          </div>
          <div className="statusbar-sep statusbar-optional" />
          <div className="statusbar-item statusbar-optional">
            <span>Engine</span>
            <span className="value">{vectorResult.engine_used}</span>
          </div>
        </>
      )}

      <div className="statusbar-status">
        {stage === 'error' && errorMessage && (
          <span style={{color:'var(--error)', fontSize:11, maxWidth:300, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>
            ⚠ {errorMessage}
          </span>
        )}
        <div className={`status-dot ${stage === 'error' ? 'error' : isWorking ? 'working' : 'ready'}`} />
        <span style={{fontSize:11, color:'var(--text-muted)'}}>
          {STAGE_LABELS[stage] ?? stage}
        </span>
        {isWorking && <span className="spinner" style={{width:10, height:10}} />}
      </div>
    </div>
  )
}

