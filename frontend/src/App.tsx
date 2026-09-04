import React, { useEffect } from 'react'
import './index.css'
import TopBar from './components/TopBar'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'
import PreviewCanvas from './components/PreviewCanvas'
import StatusBar from './components/StatusBar'
import DropZone from './components/DropZone'
import ExportModal from './components/ExportModal'
import { useAppStore } from './store/appStore'
import { uploadImage, analyzeImage } from './api/client'

function ProcessingOverlay() {
  const { stage } = useAppStore()
  const working = ['uploading','analyzing','preprocessing','quantizing','vectorizing'].includes(stage)
  if (!working) return null

  const labels: Record<string, [string, string]> = {
    uploading:     ['Uploading', 'Validating and storing your image…'],
    analyzing:     ['Analyzing', 'Detecting colors, edges, and complexity…'],
    preprocessing: ['Preprocessing', 'Applying filters and adjustments…'],
    quantizing:    ['Quantizing', 'Reducing color palette with k-means…'],
    vectorizing:   ['Vectorizing', 'Tracing raster to vector paths…'],
  }

  const [title, subtitle] = labels[stage] ?? ['Processing', 'Please wait…']

  return (
    <div className="processing-overlay">
      <div className="processing-card">
        <div style={{width:48,height:48,borderRadius:'50%',border:'3px solid var(--border-default)',borderTopColor:'var(--accent-primary)',animation:'spin 0.7s linear infinite'}} />
        <div>
          <div className="processing-title">{title}</div>
          <div className="processing-subtitle" style={{marginTop:4}}>{subtitle}</div>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" />
        </div>
      </div>
    </div>
  )
}

function App() {
  const {
    imageInfo, setStage, setImageInfo, setAnalysisResult, reset,
    mobileTab, setMobileTab, vectorResult, palette,
  } = useAppStore()

  // Global paste listener
  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile()
          if (file) {
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
              setStage('error', err?.response?.data?.detail || String(err))
            }
          }
          break
        }
      }
    }
    window.addEventListener('paste', handlePaste)
    return () => window.removeEventListener('paste', handlePaste)
  }, [])

  const hasImage = !!imageInfo

  return (
    <div className="app-layout">
      <TopBar />

      {/* Mobile Workspace Tabs (only displayed on screens <= 820px) */}
      <div className="mobile-workspace-tabs" role="tablist" aria-label="Workspace View">
        <button
          className={`mobile-tab-btn ${mobileTab === 'controls' ? 'active' : ''}`}
          onClick={() => setMobileTab('controls')}
          role="tab"
          aria-selected={mobileTab === 'controls'}
        >
          <span className="mobile-tab-icon">🎛</span> Controls
        </button>
        <button
          className={`mobile-tab-btn ${mobileTab === 'canvas' ? 'active' : ''}`}
          onClick={() => setMobileTab('canvas')}
          role="tab"
          aria-selected={mobileTab === 'canvas'}
        >
          <span className="mobile-tab-icon">👁</span> Canvas {vectorResult ? '✓' : ''}
        </button>
        <button
          className={`mobile-tab-btn ${mobileTab === 'layers' ? 'active' : ''}`}
          onClick={() => setMobileTab('layers')}
          role="tab"
          aria-selected={mobileTab === 'layers'}
        >
          <span className="mobile-tab-icon">🎨</span> Layers {palette.length > 0 ? `(${palette.length})` : ''}
        </button>
      </div>

      <div className="app-body">
        <div className={`responsive-panel-wrapper left-wrapper ${mobileTab === 'controls' ? 'mobile-visible' : ''}`}>
          <LeftPanel />
        </div>

        {/* Center Area */}
        <div className={`center-area ${mobileTab === 'canvas' ? 'mobile-visible' : ''}`}>
          {hasImage ? (
            <div style={{position:'relative', flex:1, minHeight:0, display:'flex', flexDirection:'column'}}>
              <PreviewCanvas />
              <ProcessingOverlay />
            </div>
          ) : (
            <div style={{flex:1, padding:'var(--space-6)', display:'flex', flexDirection:'column', minHeight:0}}>
              <DropZone />
            </div>
          )}
        </div>

        <div className={`responsive-panel-wrapper right-wrapper ${mobileTab === 'layers' ? 'mobile-visible' : ''}`}>
          <RightPanel />
        </div>
      </div>
      <StatusBar />
      <ExportModal />
    </div>
  )
}

export default App
