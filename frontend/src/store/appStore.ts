/**
 * VectorForge AI — Global Application State (Zustand)
 */
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type {
  ImageInfo,
  AnalysisResult,
  PaletteColor,
  VectorizeResult,
  LayerInfo,
} from '../api/client'

export type ViewMode = 'original' | 'enhanced' | 'vector'
export type ImageMode = 'auto' | 'logo' | 'photo' | 'sketch' | 'bw'
export type QualityPreset = 'fast' | 'balanced' | 'high' | 'ultra'
export type ProcessingStage = 'idle' | 'uploading' | 'analyzing' | 'preprocessing' | 'quantizing' | 'vectorizing' | 'exporting' | 'error'
export type MobileTab = 'controls' | 'canvas' | 'layers'
export type VectorizeSourceStage = 'auto' | 'original' | 'preprocessed' | 'quantized'

export interface PreprocessSettings {
  denoiseEnabled: boolean
  denoiseStrength: number
  sharpenEnabled: boolean
  sharpenStrength: number
  contrast: number
  brightness: number
  saturation: number
  bgRemovalEnabled: boolean
  bgColor: string | null
  bgTolerance: number
  bgAutoDetect: boolean
  antialiasCleanup: boolean
}

export interface VectorizeSettings {
  imageMode: ImageMode
  qualityPreset: QualityPreset
  colorPrecision: number
  layerDifference: number
  cornerThreshold: number
  lengthThreshold: number
  filterSpeckle: number
  curveFitting: 'spline' | 'polygon' | 'pixel'
  minArea: number
  simplifyTolerance: number
  groupByColor: boolean
}

export interface AppState {
  // Session
  sessionId: string | null
  stage: ProcessingStage
  errorMessage: string | null

  // Image info
  imageInfo: ImageInfo | null
  analysisResult: AnalysisResult | null

  // Processing settings
  numColors: number
  vectorizeSourceStage: VectorizeSourceStage
  preprocessSettings: PreprocessSettings
  vectorizeSettings: VectorizeSettings

  // Results
  preprocessedUrl: string | null
  quantizedUrl: string | null
  palette: PaletteColor[]
  vectorResult: VectorizeResult | null
  layers: LayerInfo[]

  // UI state
  viewMode: ViewMode
  zoom: number
  splitPosition: number
  showSplitView: boolean
  mobileTab: MobileTab
  showExportModal: boolean

  // Actions
  setStage: (stage: ProcessingStage, error?: string) => void
  setImageInfo: (info: ImageInfo) => void
  setAnalysisResult: (result: AnalysisResult) => void
  setPreprocessedUrl: (url: string) => void
  setQuantized: (palette: PaletteColor[], url: string) => void
  setVectorResult: (result: VectorizeResult) => void
  setLayers: (layers: LayerInfo[]) => void
  updatePreprocessSettings: (s: Partial<PreprocessSettings>) => void
  updateVectorizeSettings: (s: Partial<VectorizeSettings>) => void
  setNumColors: (n: number) => void
  setVectorizeSourceStage: (stage: VectorizeSourceStage) => void
  setViewMode: (mode: ViewMode) => void
  setZoom: (zoom: number | ((prev: number) => number)) => void
  setSplitPosition: (pos: number) => void
  setShowSplitView: (show: boolean) => void
  setMobileTab: (tab: MobileTab) => void
  setShowExportModal: (show: boolean) => void
  toggleLayerVisibility: (index: number) => void
  reset: () => void
}

const DEFAULT_PREPROCESS: PreprocessSettings = {
  denoiseEnabled: false,
  denoiseStrength: 3,
  sharpenEnabled: false,
  sharpenStrength: 0.5,
  contrast: 1.0,
  brightness: 1.0,
  saturation: 1.0,
  bgRemovalEnabled: false,
  bgColor: null,
  bgTolerance: 30,
  bgAutoDetect: true,
  antialiasCleanup: false,
}

const DEFAULT_VECTORIZE: VectorizeSettings = {
  imageMode: 'auto',
  qualityPreset: 'high',
  colorPrecision: 7,
  layerDifference: 12,
  cornerThreshold: 75,
  lengthThreshold: 9.0,
  filterSpeckle: 1,
  curveFitting: 'spline',
  minArea: 1.0,
  simplifyTolerance: 0.1,
  groupByColor: true,
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
  sessionId: null,
  stage: 'idle',
  errorMessage: null,
  imageInfo: null,
  analysisResult: null,
  numColors: 24,
  vectorizeSourceStage: 'auto',
  preprocessSettings: DEFAULT_PREPROCESS,
  vectorizeSettings: DEFAULT_VECTORIZE,
  preprocessedUrl: null,
  quantizedUrl: null,
  palette: [],
  vectorResult: null,
  layers: [],
  viewMode: 'original',
  zoom: 1,
  splitPosition: 50,
  showSplitView: false,
  mobileTab: 'canvas',
  showExportModal: false,

  setStage: (stage, error) =>
    set({ stage, errorMessage: error ?? null }),

  setImageInfo: (info) =>
    set({ imageInfo: info, sessionId: info.session_id, stage: 'idle', viewMode: 'original', mobileTab: 'canvas' }),

  setAnalysisResult: (result) =>
    set((state) => ({
      analysisResult: result,
      vectorizeSettings: {
        ...state.vectorizeSettings,
        imageMode: (result.recommended_mode === 'bw' || result.recommended_mode === 'sketch')
          ? result.recommended_mode
          : state.vectorizeSettings.imageMode,
        filterSpeckle: (result.recommended_mode === 'bw' || result.recommended_mode === 'sketch')
          ? 0
          : state.vectorizeSettings.filterSpeckle,
      },
    })),

  setPreprocessedUrl: (url) =>
    set({ preprocessedUrl: url }),

  setQuantized: (palette, url) =>
    set({ palette, quantizedUrl: url }),

  setVectorResult: (result) =>
    set({ vectorResult: result, layers: result.layers, mobileTab: 'canvas' }),

  setLayers: (layers) => set({ layers }),

  updatePreprocessSettings: (s) =>
    set((state) => ({ preprocessSettings: { ...state.preprocessSettings, ...s } })),

  updateVectorizeSettings: (s) =>
    set((state) => ({ vectorizeSettings: { ...state.vectorizeSettings, ...s } })),

  setNumColors: (n) => set({ numColors: n }),
  setVectorizeSourceStage: (stage) => set({ vectorizeSourceStage: stage }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setZoom: (zoom) =>
    set((state) => ({
      zoom: typeof zoom === 'function' ? zoom(state.zoom) : zoom,
    })),
  setSplitPosition: (pos) => set({ splitPosition: pos }),
  setShowSplitView: (show) => set({ showSplitView: show }),
  setMobileTab: (tab) => set({ mobileTab: tab }),
  setShowExportModal: (show) => set({ showExportModal: show }),

  toggleLayerVisibility: (index) =>
    set((state) => ({
      layers: state.layers.map((l) =>
        l.index === index ? { ...l, visible: !l.visible } : l
      ),
    })),

  reset: () =>
    set({
      sessionId: null,
      stage: 'idle',
      errorMessage: null,
      imageInfo: null,
      analysisResult: null,
      preprocessedUrl: null,
      quantizedUrl: null,
      palette: [],
      vectorResult: null,
      layers: [],
      vectorizeSourceStage: 'auto',
      viewMode: 'original',
      zoom: 1,
      mobileTab: 'canvas',
      preprocessSettings: DEFAULT_PREPROCESS,
      vectorizeSettings: DEFAULT_VECTORIZE,
    }),
  }),
  {
    name: 'vectorizer-ai-store',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        imageInfo: state.imageInfo,
        analysisResult: state.analysisResult,
        preprocessedUrl: state.preprocessedUrl,
        quantizedUrl: state.quantizedUrl,
        palette: state.palette,
        vectorResult: state.vectorResult,
        layers: state.layers,
        viewMode: state.viewMode,
        numColors: state.numColors,
        vectorizeSourceStage: state.vectorizeSourceStage,
        preprocessSettings: state.preprocessSettings,
        vectorizeSettings: state.vectorizeSettings,
      }),
    }
  )
)
