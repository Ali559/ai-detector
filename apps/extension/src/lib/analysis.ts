import type { IAnalysisResult, IVideoFrame, IVideoMeta } from '@/types'

// Dev default: the AI service directly. In production this should be the API,
// which authenticates the user and forwards to the AI service.
const ANALYSIS_URL = import.meta.env.VITE_ANALYSIS_URL ?? 'http://localhost:8000/analyze/video'

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

  const response = await fetch(ANALYSIS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => (typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)))
      .catch(() => response.statusText)
    throw new Error(`Analysis failed (${response.status}): ${detail}`)
  }
  return response.json()
}
