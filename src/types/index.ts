export interface CapturedFrame {
  timestamp: number
  data: string
  width: number
  height: number
}

export interface VideoInfo {
  width: number
  height: number
  duration: number
  src: string
}

export interface CaptureResult {
  success?: boolean
  error?: string
  videoInfo?: VideoInfo
  frames?: CapturedFrame[]
  totalFrames?: number
}

export interface ExtensionMessage {
  action: string
  frameCount?: number
}

export interface StatusState {
  message: string
  type: 'loading' | 'error' | 'success' | ''
}

export interface ITab {
  id: string;
  name: string;
}
