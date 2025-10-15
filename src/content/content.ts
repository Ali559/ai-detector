import { returnError } from '@/helpers'
import type { IExtractionResponse } from '@/types'

// Content script to find and capture frames from playing videos
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
    // Find all video elements on the page
    const videos = Array.from(document.querySelectorAll('video')) as HTMLVideoElement[]

    if (videos.length === 0) {
      return returnError('No video elements found')
    }

    // Find playing videos
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

    // Use the first playing video
    const video = playingVideos[0]

    // Create a canvas to capture frames
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    if (!ctx) {
      return returnError('Failed to create canvas context')
    }

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    const videoDuration = video.duration
    const currentTime = video.currentTime

    // Calculate frame capture intervals
    const remainingDuration = videoDuration - currentTime
    const interval = Math.max(0.5, remainingDuration / (frameCount + 1))

    for (let i = 0; i < frameCount; i++) {
      try {
        // Draw current frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

        // Convert to base64 image
        const frameData = canvas.toDataURL('image/jpeg', 1.0)

        browser.runtime.sendMessage({
          type: 'extracted',
          data: {
            data: frameData,
            width: canvas.width,
            height: canvas.height,
            timestamp: video.currentTime,
            duration: videoDuration,
            frameNumber: i + 1,
          },
        } as IExtractionResponse)
        // Wait for next frame interval if not the last frame
        if (i < frameCount - 1) {
          await seekToTime(video, Math.min(video.currentTime + interval, videoDuration - 0.1))
        }
      } catch (frameError) {
        returnError((frameError as Error).message)
      }
    }

    await browser.runtime.sendMessage({ type: 'extraction-completed' } as IExtractionResponse)
  } catch (error) {
    return returnError((error as Error).message)
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
