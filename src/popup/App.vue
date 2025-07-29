<template>
  <div class="app">
    <div class="header">
      <h2>🎬 Video Frame Capturer</h2>
    </div>

    <div class="controls">
      <div class="frame-count">
        <label for="frame-input">Frames:</label>
        <input
          id="frame-input"
          type="number"
          v-model="frameCount"
          min="1"
          max="10"
          :disabled="isCapturing"
        />
      </div>
      <button class="capture-btn" @click="captureFrames" :disabled="isCapturing">
        {{ isCapturing ? 'Capturing...' : 'Capture Frames' }}
      </button>
    </div>

    <div v-if="status.message" :class="['status', status.type]">
      {{ status.message }}
    </div>

    <div v-if="videoInfo" class="video-info">
      <div><strong>Video:</strong> {{ videoInfo.width }}×{{ videoInfo.height }}</div>
      <div><strong>Duration:</strong> {{ formatTime(videoInfo.duration) }}</div>
      <div><strong>Source:</strong> {{ getSourceName(videoInfo.src) }}</div>
    </div>

    <div v-if="capturedFrames.length > 0" class="frames-container">
      <div v-for="(frame, index) in capturedFrames" :key="index" class="frame-item">
        <img :src="frame.data" :alt="`Frame ${index + 1}`" class="frame-image" />
        <div class="frame-info">Frame {{ index + 1 }} - {{ formatTime(frame.timestamp) }}</div>
        <button class="download-btn" @click="downloadFrame(frame, index)">Download</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { CapturedFrame, VideoInfo, StatusState, CaptureResult } from '../types'

const frameCount = ref<number>(3)
const isCapturing = ref<boolean>(false)
const capturedFrames = ref<CapturedFrame[]>([])
const videoInfo = ref<VideoInfo | null>(null)

const status = reactive<StatusState>({
  message: '',
  type: '',
})

const captureFrames = async (): Promise<void> => {
  isCapturing.value = true
  capturedFrames.value = []
  videoInfo.value = null
  setStatus('Searching for playing videos...', 'loading')

  try {
    const response = (await browser.runtime.sendMessage({
      action: 'captureFrames',
      frameCount: frameCount.value,
    })) as CaptureResult

    if (response.error) {
      setStatus(response.error, 'error')
    } else if (response.success) {
      capturedFrames.value = response.frames || []
      videoInfo.value = response.videoInfo || null
      setStatus(`Successfully captured ${response.totalFrames} frames!`, 'success')
    }
  } catch (error) {
    setStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
  } finally {
    isCapturing.value = false
  }
}

const setStatus = (message: string, type: StatusState['type']): void => {
  status.message = message
  status.type = type

  if (type !== 'error') {
    setTimeout(() => {
      status.message = ''
      status.type = ''
    }, 3000)
  }
}

const formatTime = (seconds: number): string => {
  if (!seconds || isNaN(seconds)) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const getSourceName = (src: string): string => {
  if (!src || src === 'Unknown source') return 'Unknown'
  try {
    const url = new URL(src)
    return url.hostname
  } catch {
    return src.length > 30 ? src.substring(0, 30) + '...' : src
  }
}

const downloadFrame = (frame: CapturedFrame, index: number): void => {
  const link = document.createElement('a')
  link.href = frame.data
  link.download = `video-frame-${index + 1}-${Date.now()}.jpg`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.app {
  height: 700px;
  width: 500px;
}

.header {
  text-align: center;
  margin-bottom: 20px;
  color: #2c3e50;
}

.header h2 {
  font-size: 18px;
  font-weight: 600;
}

.controls {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.frame-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.frame-count label {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

input[type='number'] {
  width: 60px;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

input[type='number']:focus {
  outline: none;
  border-color: #3498db;
}

.capture-btn {
  background: #3498db;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: background-color 0.2s;
}

.capture-btn:hover:not(:disabled) {
  background: #2980b9;
}

.capture-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.status {
  text-align: center;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.status.loading {
  background: #e8f4fd;
  color: #2980b9;
}

.status.error {
  background: #fdeaea;
  color: #e74c3c;
}

.status.success {
  background: #eafaf1;
  color: #27ae60;
}

.video-info {
  background: white;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  font-size: 12px;
  color: #2c3e50;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.video-info strong {
  color: #34495e;
  font-weight: 600;
}

.video-info div {
  margin-bottom: 4px;
}

.video-info div:last-child {
  margin-bottom: 0;
}

.frames-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.frame-item {
  background: white;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.frame-item:hover {
  transform: translateY(-2px);
}

.frame-image {
  width: 100%;
  height: auto;
  border-radius: 4px;
  max-height: 120px;
  object-fit: cover;
}

.frame-info {
  font-size: 11px;
  color: #7f8c8d;
  margin: 6px 0;
  text-align: center;
  font-weight: 500;
}

.download-btn {
  background: #27ae60;
  color: white;
  border: none;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  width: 100%;
  font-weight: 500;
  transition: background-color 0.2s;
}

.download-btn:hover {
  background: #219a52;
}
</style>
