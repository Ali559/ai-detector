
// ? Essential Types
export type ResponseType = 'extract' | 'extracted' | 'extraction-completed' | 'analyse' | 'analysed' | 'error';
export type ProcessState = 'idle' | 'extracting' | 'extracted' | 'analyzing' | 'completed';


export interface IVideoFrame {
  data: Base64URLString;
  width: number;
  height: number;
  timestamp: number;
  duration: number;
  frameNumber: number
}


export interface IAction {
  type: ResponseType;
  frameCount: number
}

export interface IExtractionResponse {
  type: ResponseType;
  data?: IVideoFrame
  error?: string
}

// * Non-Essential types

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

