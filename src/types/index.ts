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

export interface InuptType {
  id: string;
  label: string;
  placeHolder: string;
  type: 'text' | 'password' | 'email' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local' | 'week' | 'month' | 'color' | 'checkbox' | 'radio' | 'file' | 'range' | 'select-one' | 'select-multiple' | 'submit' | 'reset' | 'button' | 'image' | 'hidden' | 'textarea';
}


export interface IUser {
  id: string;
  name: string;
  email: string;
}

export interface IStep {
  id: string;
  title: string;
  description?: string;
}

export type ProcessState = 'idle' | 'extracting' | 'extracted' | 'analyzing' | 'completed';

