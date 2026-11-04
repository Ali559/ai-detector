import { returnError } from '@/helpers'
import type { IExtractionResponse } from '@/types'

/**
 * Content script: Capture representative frames from any playing video element.
 */
browser.runtime.onMessage.addListener(async (message): Promise<unknown> => {
  if (message.type === 'start') {
    try {
      return await captureVideoFrames(message.frameCount || 3)
    } catch (error) {
      returnError((error as Error).message)
      return
    }
  }

  returnError('Unknown action')
  return
})

async function captureVideoFrames(frameCount: number): Promise<unknown> {
  try {
    const videos = findAllVideos()

    if (videos.length === 0) {
      return returnError('No video elements found')
    }

    // Filter for currently playing videos
    const playingVideos = videos.filter(
      (video) =>
        !video.paused &&
        !video.ended &&
        video.readyState >= 2 &&
        video.videoWidth > 0 &&
        video.videoHeight > 0,
    )

    if (playingVideos.length === 0) {
      return returnError('No playing videos found')
    }

    // Use the first detected playing video
    const video = playingVideos[0]
    const videoFingerprint = crypto.randomUUID()

    // Create canvas and context for frame capture
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      return returnError('Failed to create canvas context')
    }

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const videoDuration = video.duration
    const currentTime = video.currentTime

    // Cap sampling to a maximum window (e.g., 30 s to limit processing)
    const MAX_SAMPLE_WINDOW = 30
    const remainingDuration = Math.min(videoDuration - currentTime, MAX_SAMPLE_WINDOW)

    // Calculate capture interval (≥0.5 s between frames)
    const interval = Math.max(0.5, remainingDuration / (frameCount + 1))

    const seenHashes = new Set<string>()
    const originalTime = video.currentTime

    for (let i = 0; i < frameCount; i++) {
      try {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert to compressed Base64 JPEG
        const frameData = canvas.toDataURL('image/jpeg', 0.8)

        // Deduplicate frames by SHA-256 of Base64
        const frameHash = await digestSHA256(frameData)
        if (seenHashes.has(frameHash)) {
          console.debug(`[Frame ${i + 1}] skipped (duplicate)`)
        } else {
          seenHashes.add(frameHash)

          await browser.runtime.sendMessage({
            type: 'extracted',
            videoId: videoFingerprint,
            data: {
              data: frameData,
              width: canvas.width,
              height: canvas.height,
              timestamp: video.currentTime,
              duration: videoDuration,
              frameNumber: i + 1,
            },
          } as IExtractionResponse)
        }

        // Move to next sample point
        if (i < frameCount - 1) {
          await seekToTime(video, Math.min(video.currentTime + interval, videoDuration - 0.1))
        }
      } catch (frameError) {
        returnError((frameError as Error).message)
      }
    }

    await browser.runtime.sendMessage({
      type: 'extraction-completed',
      videoId: videoFingerprint,
      frameCount,
    } as IExtractionResponse)

    // Optional: restore playback position and clean up
    video.currentTime = originalTime
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    canvas.remove()
  } catch (error) {
    return returnError((error as Error).message)
  }
}

/**
 * Wait until the target time is reached and frame is rendered.
 */
function seekToTime(video: HTMLVideoElement, targetTime: number): Promise<void> {
  return new Promise((resolve) => {
    const onSeeked = () => {
      video.removeEventListener('seeked', onSeeked)
      // Allow brief render delay before capture
      setTimeout(resolve, 100)
    }
    video.addEventListener('seeked', onSeeked)
    video.currentTime = targetTime
  })
}

/**
 * SHA-256 hash generator for frame deduplication.
 */
async function digestSHA256(data: string): Promise<string> {
  const buffer = new TextEncoder().encode(data)
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
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
