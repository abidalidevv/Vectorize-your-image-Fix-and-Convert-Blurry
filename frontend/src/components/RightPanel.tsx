import React, { useState } from 'react'
import { useAppStore } from '../store/appStore'

type RightSection = 'palette' | 'layers' | 'stats'

export default function RightPanel() {
  const {
    palette, vectorResult, layers, toggleLayerVisibility,
    imageInfo, activeTool, enhancedResult, bgRemovedResult,
  } = useAppStore()

  const [activeTab, setActiveTab] = useState<RightSection>('palette')

  const stats = vectorResult?.stats

  const formatBytes = (b: number) => {
    if (b > 1024 * 1024) return `${(b / 1024 / 1024).toFixed(2)} MB`
    if (b > 1024) return `${(b / 1024).toFixed(1)} KB`
    return `${b} B`
  }

  // ── Tool: Image Enhancer Info ───────────────────────────────────────────
  if (activeTool === 'enhancer') {
    return (
      <div className="right-panel">
        <div style={{padding:'var(--space-4)', borderBottom:'1px solid var(--border-subtle)'}}>
          <div className="panel-section-title">✨ Enhancer Studio</div>
          <div style={{fontSize:11, color:'var(--text-muted)', marginTop:2}}>
            High-Resolution Upscaling & Clarity
          </div>
        </div>

        <div className="panel-scroll" style={{padding:'var(--space-4)'}}>
          <div className="image-info-card">
            <div className="image-info-row">
              <span className="image-info-label">Original Res</span>
              <span className="image-info-value">{imageInfo ? `${imageInfo.width} × ${imageInfo.height} px` : '—'}</span>
            </div>
            <div className="image-info-row">
              <span className="image-info-label">Enhanced Res</span>
              <span className="image-info-value" style={{color: enhancedResult ? 'var(--success)' : 'inherit'}}>
                {enhancedResult ? `${enhancedResult.width} × ${enhancedResult.height} px` : 'Pending…'}
              </span>
            </div>
            <div className="image-info-row">
              <span className="image-info-label">Magnification</span>
              <span className="image-info-value">
                {enhancedResult && imageInfo ? `${Math.round(enhancedResult.width / imageInfo.width)}× HD` : '1×'}
              </span>
            </div>
          </div>

          {enhancedResult && (
            <div style={{marginTop: 16}}>
              <div className="panel-section-title" style={{marginBottom: 8, fontSize: 12}}>
                Applied Pipeline
              </div>
              <div style={{display:'flex', flexDirection:'column', gap: 6}}>
                {enhancedResult.changesApplied.map((c, i) => (
                  <div key={i} style={{
                    fontSize: 11,
                    padding: '6px 10px',
                    borderRadius: 6,
                    background: 'rgba(16,185,129,0.1)',
                    border: '1px solid rgba(16,185,129,0.25)',
                    color: '#10b981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}>
                    <span>✓</span>
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── Tool: Remove BG Info ────────────────────────────────────────────────
  if (activeTool === 'bgremover') {
    return (
      <div className="right-panel">
        <div style={{padding:'var(--space-4)', borderBottom:'1px solid var(--border-subtle)'}}>
          <div className="panel-section-title">✂️ Remove BG Studio</div>
          <div style={{fontSize:11, color:'var(--text-muted)', marginTop:2}}>
            Cutout & Background Isolation
          </div>
        </div>

        <div className="panel-scroll" style={{padding:'var(--space-4)'}}>
          <div className="image-info-card">
            <div className="image-info-row">
              <span className="image-info-label">Status</span>
              <span className={`image-info-value ${bgRemovedResult ? 'text-success' : ''}`}>
                {bgRemovedResult ? 'Cutout Ready ✓' : 'Awaiting Action'}
              </span>
            </div>
            <div className="image-info-row">
              <span className="image-info-label">Resolution</span>
              <span className="image-info-value">
                {imageInfo ? `${imageInfo.width} × ${imageInfo.height} px` : '—'}
              </span>
            </div>
            <div className="image-info-row">
              <span className="image-info-label">Format</span>
              <span className="image-info-value" title="PNG with Alpha Transparency">PNG (Alpha)</span>
            </div>
          </div>

          {bgRemovedResult && (
            <div style={{marginTop: 16}}>
              <div className="panel-section-title" style={{marginBottom: 8, fontSize: 12}}>
                Processing Operations
              </div>
              <div style={{display:'flex', flexDirection:'column', gap: 6}}>
                {bgRemovedResult.changesApplied.map((c, i) => (
                  <div key={i} style={{
                    fontSize: 11,
                    padding: '6px 10px',
                    borderRadius: 6,
                    background: 'rgba(245,158,11,0.1)',
                    border: '1px solid rgba(245,158,11,0.25)',
                    color: '#f59e0b',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6
                  }}>
                    <span>✓</span>
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ── Tool: Vectorizer (Palette, Layers, Stats) ───────────────────────────
  return (
    <div className="right-panel">
      {/* Tab selector */}
      <div style={{
        display:'flex', gap:2, padding:'var(--space-2)',
        borderBottom:'1px solid var(--border-subtle)',
      }}>
        {(['palette', 'layers', 'stats'] as RightSection[]).map(tab => (
          <button
            key={tab}
            className={`segment-tab ${activeTab === tab ? 'active' : ''}`}
            style={{fontSize:11}}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <div className="panel-scroll">
        {/* ── Palette Tab ─────────────────────────────────────────────── */}
        {activeTab === 'palette' && (
          <div>
            <div className="panel-section-title" style={{marginBottom:'var(--space-3)'}}>
              Color Palette
            </div>

            {palette.length === 0 ? (
              <div style={{color:'var(--text-muted)', fontSize:12, textAlign:'center', padding:'var(--space-6) 0'}}>
                Run color quantization to see palette
              </div>
            ) : (
              <>
                {/* Color grid */}
                <div className="palette-grid" style={{marginBottom:'var(--space-3)'}}>
                  {palette.map(c => (
                    <div
                      key={c.index}
                      className={`palette-swatch ${!c.enabled ? 'disabled' : ''}`}
                      style={{ background: c.hex }}
                      title={`${c.hex} — ${c.percentage.toFixed(1)}%`}
                    />
                  ))}
                </div>

                {/* Detailed list */}
                <div className="palette-list">
                  {palette.map(c => (
                    <div key={c.index} className="palette-item">
                      <div
                        className="palette-item-swatch"
                        style={{ background: c.hex }}
                      />
                      <span className="palette-item-hex">{c.hex}</span>
                      <span className="palette-item-pct">{c.percentage.toFixed(1)}%</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Layers Tab ──────────────────────────────────────────────── */}
        {activeTab === 'layers' && (
          <div>
            <div className="panel-section-title" style={{marginBottom:'var(--space-3)'}}>
              Vector Layers
            </div>

            {layers.length === 0 ? (
              <div style={{color:'var(--text-muted)', fontSize:12, textAlign:'center', padding:'var(--space-6) 0'}}>
                Vectorize to see color layers
              </div>
            ) : (
              <div style={{display:'flex', flexDirection:'column', gap:2}}>
                {layers.map(layer => (
                  <div
                    key={layer.index}
                    className={`layer-item ${!layer.visible ? 'hidden' : ''}`}
                    onClick={() => toggleLayerVisibility(layer.index)}
                    title={`Click to toggle visibility`}
                  >
                    <div
                      className="layer-item-color"
                      style={{ background: layer.color_hex }}
                    />
                    <span className="layer-item-name">{layer.label}</span>
                    <span className="layer-item-paths">{layer.path_count}p</span>
                    <span className="layer-item-visibility">
                      {layer.visible ? '👁' : '🚫'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Stats Tab ───────────────────────────────────────────────── */}
        {activeTab === 'stats' && (
          <div>
            <div className="panel-section-title" style={{marginBottom:'var(--space-3)'}}>
              SVG Statistics
            </div>

            {!stats ? (
              <div style={{color:'var(--text-muted)', fontSize:12, textAlign:'center', padding:'var(--space-6) 0'}}>
                Vectorize to see statistics
              </div>
            ) : (
              <>
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-value">{stats.path_count}</div>
                    <div className="stat-label">Paths</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{stats.group_count}</div>
                    <div className="stat-label">Groups</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{stats.color_count}</div>
                    <div className="stat-label">Colors</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{formatBytes(stats.file_size_bytes)}</div>
                    <div className="stat-label">SVG Size</div>
                  </div>
                </div>

                <div style={{marginTop:'var(--space-3)'}}>
                  <div className="image-info-card">
                    <div className="image-info-row">
                      <span className="image-info-label">Dimensions</span>
                      <span className="image-info-value">{stats.width} × {stats.height}</span>
                    </div>
                    <div className="image-info-row">
                      <span className="image-info-label">ViewBox</span>
                      <span className={`image-info-value ${stats.has_viewbox ? 'text-success' : 'text-error'}`}>
                        {stats.has_viewbox ? 'Present ✓' : 'Missing ✗'}
                      </span>
                    </div>
                    <div className="image-info-row">
                      <span className="image-info-label">Raster in SVG</span>
                      <span className={`image-info-value ${stats.contains_raster ? 'text-error' : 'text-success'}`}>
                        {stats.contains_raster ? 'YES (⚠ not pure vector)' : 'No ✓'}
                      </span>
                    </div>
                    <div className="image-info-row">
                      <span className="image-info-label">Engine</span>
                      <span className="image-info-value">{vectorResult?.engine_used}</span>
                    </div>
                    <div className="image-info-row">
                      <span className="image-info-label">Process Time</span>
                      <span className="image-info-value">{vectorResult?.processing_time_ms}ms</span>
                    </div>
                  </div>
                </div>

                {/* Validation warnings */}
                {stats.contains_raster && (
                  <div className="alert alert-warning" style={{marginTop:'var(--space-3)'}}>
                    ⚠ SVG contains embedded raster. Try different settings.
                  </div>
                )}
                {!stats.has_viewbox && (
                  <div className="alert alert-warning" style={{marginTop:'var(--space-3)'}}>
                    ⚠ SVG missing viewBox attribute
                  </div>
                )}
                {stats.path_count === 0 && (
                  <div className="alert alert-error" style={{marginTop:'var(--space-3)'}}>
                    ✗ No vector paths found in SVG
                  </div>
                )}
                {!stats.contains_raster && stats.path_count > 0 && (
                  <div className="alert alert-success" style={{marginTop:'var(--space-3)'}}>
                    ✓ Valid pure vector SVG
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
