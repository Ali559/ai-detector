import { apiFetch } from '@/lib/api'
import type { IAnalysisResult, IVideoFrame, IVideoMeta } from '@/types'

/** Send captured frames to the API, which checks the user's quota and runs the AI service. */
export async function analyzeFrames(
  frames: IVideoFrame[],
  meta: IVideoMeta | null,
  signal?: AbortSignal,
): Promise<IAnalysisResult> {
  const sparse = frames.filter((f) => f.kind === 'sparse')
  const bursts = new Map<number, IVideoFrame[]>()
  for (const frame of frames) {
    if (frame.kind !== 'burst') continue
    const index = frame.burstIndex ?? 0
    bursts.set(index, [...(bursts.get(index) ?? []), frame])
  }

  return apiFetch<IAnalysisResult>('/detections', {
    method: 'POST',
    signal,
    body: JSON.stringify({
      video: {
        page_url: meta?.pageUrl,
        width: meta?.width,
        height: meta?.height,
        duration: meta?.duration,
        capture_method: meta?.captureMethod ?? sparse[0]?.captureMethod ?? 'canvas',
      },
      frames: sparse.map((f) => ({ data: f.data, timestamp: f.timestamp })),
      bursts: [...bursts.values()].map((burst) => ({
        fps: meta?.burstFps ?? 8,
        frames: burst.map((f) => ({ data: f.data, timestamp: f.timestamp })),
      })),
    }),
  })
}
