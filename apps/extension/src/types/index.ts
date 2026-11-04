// ? AI service result types (apps/ai_service/app/schemas.py)
export type Verdict = 'likely_ai' | 'inconclusive' | 'no_evidence'

export interface IHeadResult {
  name: 'face' | 'scene' | 'temporal' | string
  model: string
  available: boolean
  score: number | null
  peak: number | null
  frames_scored: number
  calibrated: boolean
  reason: string | null
  details: Record<string, unknown>
}

export interface IAnalysisResult {
  verdict: Verdict
  probability: number | null
  calibrated: boolean
  reasons: string[]
  heads: IHeadResult[]
  quality: {
    total_frames: number
    usable_frames: number
    usable_bursts: number
    poor: boolean
    flags: string[]
  }
  frame_hashes: string[]
  processing_time_ms: number
}

// ? Essential Types
export type ResponseType =
  | 'start'
  | 'extracted'
  | 'extraction-completed'
  | 'capture-visible-tab'
  | 'error'
export type ProcessState = 'idle' | 'extracting' | 'extracted' | 'analyzing' | 'completed'

/** 'canvas' reads decoded pixels; 'tab_capture' screenshots the tab when the canvas is tainted. */
export type CaptureMethod = 'canvas' | 'tab_capture'

export interface IVideoFrame {
  data: Base64URLString
  width: number
  height: number
  timestamp: number
  duration: number
  frameNumber: number
  /** 'sparse' frames are spread across the video; 'burst' frames are consecutive at BURST_FPS. */
  kind: 'sparse' | 'burst'
  burstIndex?: number
  captureMethod: CaptureMethod
}

export interface IVideoMeta {
  pageUrl: string
  width: number
  height: number
  duration: number | null
  captureMethod: CaptureMethod
  burstFps: number
}

export interface IAction {
  type: ResponseType
  frameCount: number
}

export interface IExtractionResponse {
  type: ResponseType
  videoId?: string
  data?: IVideoFrame
  meta?: IVideoMeta
  frameCount?: number
  error?: string
}

// * Non-Essential types

export interface ITab {
  id: string
  name: string
}

export interface InuptType {
  id: string
  label: string
  placeHolder: string
  type:
    | 'text'
    | 'password'
    | 'email'
    | 'number'
    | 'tel'
    | 'url'
    | 'search'
    | 'date'
    | 'time'
    | 'datetime-local'
    | 'week'
    | 'month'
    | 'color'
    | 'checkbox'
    | 'radio'
    | 'file'
    | 'range'
    | 'select-one'
    | 'select-multiple'
    | 'submit'
    | 'reset'
    | 'button'
    | 'image'
    | 'hidden'
    | 'textarea'
}

export interface IUser {
  id: string
  name: string
  email: string
}
