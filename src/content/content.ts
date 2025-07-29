import type { ExtensionMessage, CaptureResult, CapturedFrame, VideoInfo } from '../types'

// Content script to find and capture frames from playing videos
browser.runtime.onMessage.addListener(
  async (message: ExtensionMessage): Promise<CaptureResult> => {
    if (message.action === 'findAndCaptureVideos') {
      try {
        const result = await captureVideoFrames(message.frameCount || 3)
        return result
      } catch (error) {
        console.error('Content script error:', error)
        return { error: error instanceof Error ? error.message : 'Unknown error occurred' }
      }
    }

    return { error: 'Unknown action' }
  }
)

async function captureVideoFrames(frameCount: number): Promise<CaptureResult> {
  try {
    // Find all video elements on the page
    const videos = Array.from(document.querySelectorAll('video')) as HTMLVideoElement[]

    if (videos.length === 0) {
      return { error: 'No video elements found on this page' }
    }

    // Find playing videos
    const playingVideos = videos.filter(video =>
      !video.paused &&
      !video.ended &&
      video.readyState >= 2 &&
      video.videoWidth > 0 &&
      video.videoHeight > 0
    )

    if (playingVideos.length === 0) {
      return { error: 'No currently playing videos found' }
    }

    // Use the first playing video
    const video = playingVideos[0]
    const frames: CapturedFrame[] = []

    // Create a canvas to capture frames
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      return { error: 'Failed to create canvas context' }
    }

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const videoDuration = video.duration
    const currentTime = video.currentTime

    // Store original time to restore later
    const originalTime = currentTime

    // Calculate frame capture intervals
    const remainingDuration = videoDuration - currentTime
    const interval = Math.max(0.5, remainingDuration / (frameCount + 1))

    for (let i = 0; i < frameCount; i++) {
      try {
        // Draw current frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert to base64 image
        const frameData = canvas.toDataURL('image/jpeg', 0.8)

        frames.push({
          timestamp: video.currentTime,
          data: frameData,
          width: canvas.width,
          height: canvas.height
        })

        // Wait for next frame interval if not the last frame
        if (i < frameCount - 1) {
          await seekToTime(video, Math.min(video.currentTime + interval, videoDuration - 0.1))
        }
      } catch (frameError) {
        console.warn('Failed to capture frame:', frameError)
      }
    }

    // Restore original video time
    video.currentTime = originalTime

    const videoInfo: VideoInfo = {
      width: video.videoWidth,
      height: video.videoHeight,
      duration: video.duration,
      src: video.src || video.currentSrc || 'Unknown source'
    }

    return {
      success: true,
      videoInfo,
      frames,
      totalFrames: frames.length
    }

  } catch (error) {
    return { error: `Failed to capture frames: ${error instanceof Error ? error.message : 'Unknown error'}` }
  }
}

function seekToTime(video: HTMLVideoElement, targetTime: number): Promise<void> {
  return new Promise((resolve) => {
    const onSeeked = () => {
      video.removeEventListener('seeked', onSeeked)
      // Small delay to ensure frame is rendered
      setTimeout(resolve, 100)
    }

    video.addEventListener('seeked', onSeeked)
    video.currentTime = targetTime
  })
}
