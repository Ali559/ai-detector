import { returnError } from '@/helpers'
import type { CaptureMethod, IExtractionResponse, IVideoFrame } from '@/types'

/**
 * Content script: capture frames from the playing video for analysis.
 *
 * Two kinds of frames are captured (see docs/ai-video-detection-research.md):
 * - sparse frames spread across the whole video, for the per-frame detectors;
 * - bursts of consecutive frames at BURST_FPS during normal playback, for the
 *   temporal detector (D3 expects 16 frames at 8 fps).
 */

const BURST_FPS = 8
const BURST_LENGTH = 16
const JPEG_QUALITY = 0.95
const MAX_LONG_SIDE = 1920
const SEEK_TIMEOUT_MS = 5000
// Chrome allows ~2 captureVisibleTab calls per second.
const TAB_CAPTURE_INTERVAL_MS = 600

browser.runtime.onMessage.addListener(async (message): Promise<unknown> => {
  if (message.type === 'start') {
    try {
      return await captureVideoFrames(message.frameCount || 16)
    } catch (error) {
      returnError((error as Error).message)
      return
    }
  }
})

async function captureVideoFrames(frameCount: number): Promise<unknown> {
  const video = findAllVideos().find(
    (v) => !v.paused && !v.ended && v.readyState >= 2 && v.videoWidth > 0 && v.videoHeight > 0,
  )
  if (!video) return returnError('No playing videos found')

  const videoId = crypto.randomUUID()
  const grabber = new FrameGrabber(video)
  const duration = Number.isFinite(video.duration) ? video.duration : null
  const originalTime = video.currentTime
  let frameNumber = 0

  const send = (frame: Omit<IVideoFrame, 'frameNumber' | 'duration' | 'captureMethod'>) =>
    browser.runtime.sendMessage({
      type: 'extracted',
      videoId,
      data: {
        ...frame,
        frameNumber: ++frameNumber,
        duration: duration ?? 0,
        captureMethod: grabber.method,
      },
    } as IExtractionResponse)

  // Probe once so a tainted canvas switches to tab capture before we start.
  await grabber.grab()
  let burstCount = 0

  try {
    // Burst 1 at the current position: no seek needed.
    if (grabber.method === 'canvas' && (await captureBurst(video, grabber, burstCount, send))) {
      burstCount++
    }

    // Sparse frames across the video, skipping the first and last 2%.
    const seen = new Set<string>()
    for (let i = 0; i < frameCount; i++) {
      if (duration !== null) {
        // A seek that times out (slow stream) just costs us that frame.
        if (!(await trySeek(video, duration * (0.02 + (0.96 * (i + 0.5)) / frameCount)))) continue
      } else if (i > 0) {
        await wait(1000) // Live stream: sample during playback.
      }
      const frame = await grabber.grab()
      if (seen.has(frame.data)) continue
      seen.add(frame.data)
      await send({ ...frame, kind: 'sparse' })
    }

    // Burst 2 further into the video, if it is long enough to differ.
    if (grabber.method === 'canvas' && duration !== null && duration >= 20) {
      if (
        (await trySeek(video, duration * 0.6)) &&
        (await captureBurst(video, grabber, burstCount, send))
      ) {
        burstCount++
      }
    }
  } finally {
    // We only ever start on a playing video, so leave it playing where it was.
    await trySeek(video, originalTime)
    await video.play().catch(() => undefined)
  }

  await browser.runtime.sendMessage({
    type: 'extraction-completed',
    videoId,
    frameCount: frameNumber,
    meta: {
      pageUrl: location.href,
      width: video.videoWidth,
      height: video.videoHeight,
      duration,
      captureMethod: grabber.method,
      burstFps: BURST_FPS,
    },
  } as IExtractionResponse)
}

/**
 * Capture BURST_LENGTH frames at BURST_FPS of media time while the video plays.
 * Returns false (and sends nothing) if playback stalls before the burst fills.
 */
async function captureBurst(
  video: HTMLVideoElement,
  grabber: FrameGrabber,
  burstIndex: number,
  send: (
    frame: Omit<IVideoFrame, 'frameNumber' | 'duration' | 'captureMethod'>,
  ) => Promise<unknown>,
): Promise<boolean> {
  if (video.paused) await video.play()
  const interval = 1 / BURST_FPS
  const frames: Awaited<ReturnType<FrameGrabber['grab']>>[] = []
  // Targets sit on a fixed BURST_FPS grid from the first frame, so the burst
  // averages BURST_FPS even when the video's own rate doesn't divide evenly.
  // A frame within half a 60 fps frame of its target counts as on time.
  const tolerance = 1 / 120
  let start: number | null = null

  await new Promise<void>((resolve) => {
    const deadline = setTimeout(resolve, (BURST_LENGTH / BURST_FPS) * 3000 + 2000)
    const done = () => {
      clearTimeout(deadline)
      resolve()
    }
    const onFrame = async (mediaTime: number) => {
      start ??= mediaTime
      if (mediaTime >= start + frames.length * interval - tolerance) {
        frames.push(await grabber.grab(mediaTime))
      }
      if (frames.length >= BURST_LENGTH || video.ended) return done()
      schedule()
    }
    const schedule = () => {
      if ('requestVideoFrameCallback' in video) {
        video.requestVideoFrameCallback((_now, meta) => onFrame(meta.mediaTime))
      } else {
        setTimeout(() => onFrame((video as HTMLVideoElement).currentTime), (interval * 1000) / 2)
      }
    }
    schedule()
  })

  if (frames.length < BURST_LENGTH) return false
  for (const frame of frames) await send({ ...frame, kind: 'burst', burstIndex })
  return true
}

/** Reads the current frame from the canvas, or from a tab screenshot if the canvas is tainted. */
class FrameGrabber {
  method: CaptureMethod = 'canvas'
  private canvas = document.createElement('canvas')
  private ctx = this.canvas.getContext('2d')!
  private lastTabCapture = 0

  constructor(private video: HTMLVideoElement) {
    const scale = Math.min(1, MAX_LONG_SIDE / Math.max(video.videoWidth, video.videoHeight))
    this.canvas.width = Math.round(video.videoWidth * scale)
    this.canvas.height = Math.round(video.videoHeight * scale)
  }

  async grab(timestamp = this.video.currentTime) {
    if (this.method === 'canvas') {
      try {
        this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height)
        return this.frame(timestamp)
      } catch (error) {
        if ((error as Error).name !== 'SecurityError') throw error
        this.method = 'tab_capture'
      }
    }
    await this.drawFromTab()
    return this.frame(timestamp)
  }

  private frame(timestamp: number) {
    return {
      data: this.canvas.toDataURL('image/jpeg', JPEG_QUALITY),
      width: this.canvas.width,
      height: this.canvas.height,
      timestamp,
    }
  }

  private async drawFromTab() {
    const rect = this.video.getBoundingClientRect()
    const left = Math.max(rect.left, 0)
    const top = Math.max(rect.top, 0)
    const right = Math.min(rect.right, window.innerWidth)
    const bottom = Math.min(rect.bottom, window.innerHeight)
    if (right - left < 64 || bottom - top < 64) {
      throw new Error('This video blocks direct capture. Scroll it fully into view and retry.')
    }

    await wait(this.lastTabCapture + TAB_CAPTURE_INTERVAL_MS - Date.now())
    this.lastTabCapture = Date.now()
    const dataUrl: string = await browser.runtime.sendMessage({ type: 'capture-visible-tab' })
    const image = await loadImage(dataUrl)

    const scale = image.naturalWidth / window.innerWidth
    const [sx, sy, sw, sh] = [left, top, right - left, bottom - top].map((v) => v * scale)
    this.canvas.width = Math.round(sw)
    this.canvas.height = Math.round(sh)
    this.ctx.drawImage(image, sx, sy, sw, sh, 0, 0, this.canvas.width, this.canvas.height)
  }
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('Failed to read tab capture'))
    image.src = src
  })
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, Math.max(0, ms)))
}

/**
 * Seek and wait until the frame at the target time is decoded.
 */
function seekTo(video: HTMLVideoElement, targetTime: number): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      video.removeEventListener('seeked', onSeeked)
      reject(new Error('Timed out seeking the video'))
    }, SEEK_TIMEOUT_MS)
    const onSeeked = () => {
      clearTimeout(timer)
      video.removeEventListener('seeked', onSeeked)
      // Allow brief render delay before capture
      setTimeout(resolve, 100)
    }
    video.addEventListener('seeked', onSeeked)
    video.currentTime = targetTime
  })
}

function trySeek(video: HTMLVideoElement, targetTime: number): Promise<boolean> {
  return seekTo(video, targetTime).then(
    () => true,
    () => false,
  )
}

/**
 * Retrieve all <video> elements, including those inside shadow DOMs.
 */
function findAllVideos(): HTMLVideoElement[] {
  const collect = (root: Document | ShadowRoot): HTMLVideoElement[] => {
    const elements = Array.from(root.querySelectorAll('video')) as HTMLVideoElement[]
    const shadowVideos = Array.from(root.querySelectorAll('*'))
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      .filter((el): el is HTMLElement & { shadowRoot: ShadowRoot } => !!(el as any).shadowRoot)
      .flatMap((el) => collect(el.shadowRoot))
    return [...elements, ...shadowVideos]
  }
  return collect(document)
}
