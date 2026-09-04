/**
 * VectorForge AI — API Client
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/',
  timeout: 120000,
})

export interface ImageInfo {
  session_id: string
  filename: string
  width: number
  height: number
  file_size_bytes: number
  format: string
  has_alpha: boolean
  mode: string
  preview_url: string
}

export interface AnalysisResult {
  session_id: string
  recommended_mode: 'logo' | 'photo' | 'sketch' | 'bw'
  confidence: number
  color_count_estimate: number
  dominant_colors: Array<{ hex: string; rgb: number[]; percentage: number; index: number }>
  is_grayscale: boolean
  has_transparency: boolean
  edge_density: number
  complexity_score: number
  saturation_mean: number
  notes: string
}

export interface PaletteColor {
  index: number
  hex: string
  rgb: number[]
  percentage: number
  enabled: boolean
  is_background: boolean
}

export interface QuantizeResult {
  session_id: string
  num_colors: number
  palette: PaletteColor[]
  preview_url: string
}

export interface SVGStats {
  path_count: number
  group_count: number
  color_count: number
  file_size_bytes: number
  width: number
  height: number
  has_viewbox: boolean
  contains_raster: boolean
}

export interface LayerInfo {
  index: number
  color_hex: string
  color_rgb: number[]
  path_count: number
  visible: boolean
  label: string
}

export interface VectorizeResult {
  session_id: string
  svg_url: string
  svg_data_url: string
  stats: SVGStats
  layers: LayerInfo[]
  engine_used: string
  processing_time_ms: number
}

export interface PreprocessResult {
  session_id: string
  preview_url: string
  changes_applied: string[]
}

// ── Upload ─────────────────────────────────────────────────────────────────
export async function uploadImage(file: File): Promise<ImageInfo> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<ImageInfo>('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// ── Analyze ────────────────────────────────────────────────────────────────
export async function analyzeImage(sessionId: string): Promise<AnalysisResult> {
  const { data } = await api.post<AnalysisResult>('/api/analyze', { session_id: sessionId })
  return data
}

// ── Preprocess ─────────────────────────────────────────────────────────────
export async function preprocessImage(params: {
  session_id: string
  denoise_enabled?: boolean
  denoise_strength?: number
  sharpen_enabled?: boolean
  sharpen_strength?: number
  contrast?: number
  brightness?: number
  saturation?: number
  bg_removal_enabled?: boolean
  bg_color?: string | null
  bg_tolerance?: number
  bg_auto_detect?: boolean
  antialias_cleanup?: boolean
}): Promise<PreprocessResult> {
  const { data } = await api.post<PreprocessResult>('/api/preprocess', params)
  return data
}

// ── Quantize ───────────────────────────────────────────────────────────────
export async function quantizeImage(params: {
  session_id: string
  num_colors: number
  method?: 'kmeans' | 'median_cut' | 'auto'
  use_preprocessed?: boolean
}): Promise<QuantizeResult> {
  const { data } = await api.post<QuantizeResult>('/api/quantize', params)
  return data
}

// ── Vectorize ──────────────────────────────────────────────────────────────
export async function vectorizeImage(params: {
  session_id: string
  image_mode?: string
  quality_preset?: string
  color_precision?: number
  layer_difference?: number
  corner_threshold?: number
  length_threshold?: number
  max_iterations?: number
  splice_threshold?: number
  filter_speckle?: number
  curve_fitting?: string
  min_area?: number
  simplify_tolerance?: number
  group_by_color?: boolean
  remove_background?: boolean
}): Promise<VectorizeResult> {
  const { data } = await api.post<VectorizeResult>('/api/vectorize', params)
  return data
}

// ── Export ─────────────────────────────────────────────────────────────────
export async function exportSVG(sessionId: string, optimize = true): Promise<Blob> {
  const { data } = await api.post(
    '/api/export/svg',
    { session_id: sessionId, optimize },
    { responseType: 'blob' }
  )
  return data
}

export async function exportPNG(
  sessionId: string,
  scale: 1 | 2 | 4 | 8 = 1,
  backgroundColorHex?: string
): Promise<Blob> {
  const { data } = await api.post(
    '/api/export/png',
    {
      session_id: sessionId,
      scale,
      background_color: backgroundColorHex || null,
    },
    { responseType: 'blob' }
  )
  return data
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/api/session/${sessionId}`)
}

export default api
