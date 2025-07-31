<script setup lang="ts">
import IdleCard from './IdleCard.vue'
import ExtractingCard from './ExtractingCard.vue'
import ExtractedCard from './ExtractedCard.vue'
import AnalysisInProgressCard from './AnalysisInProgressCard.vue'
import AnalysisCompleteCard from './AnalysisCompleteCard.vue'
import type { ProcessState } from '@/types'
import { ref } from 'vue'
import { useFramesStore } from '@/store/framesStore'
import { FileWarningIcon } from 'lucide-vue-next'
import AlertComponent from '@/components/atoms/AlertComponent.vue'

const currentStep = ref<ProcessState>('idle')

const { addFrame, frames } = useFramesStore()
const error = ref<string | undefined>('')

browser.runtime.onMessage.addListener((message) => {
  if (message.action === 'frameCaptured') {
    console.log(message)

    addFrame({
      data: message.frameData,
      timestamp: message.timestamp,
      width: message.width,
      height: message.height,
    })
    currentStep.value = 'extracting'
  }
})
const captureFrames = async (frameCount: number) => {
  await browser.runtime.sendMessage({
    action: 'captureFrames',
    frameCount: frameCount,
  })
}
</script>
<template>
  <div class="flex-1 p-4 overflow-y-auto space-y-4">
    <AlertComponent
      v-if="error"
      title="Error Capturing Frames"
      :icon="FileWarningIcon"
      :description="error"
    />
    <!-- Extract Video Frames -->
    <IdleCard v-if="currentStep === 'idle'" @capture-frames="captureFrames" />

    <!-- Extracting Frames... -->
    <ExtractingCard v-if="currentStep === 'extracting'" :frames="frames" />

    <!-- Extracted Frames -->
    <ExtractedCard v-if="currentStep === 'extracted'" />

    <!-- Analysis in Progress -->
    <AnalysisInProgressCard v-if="currentStep === 'analyzing'" />

    <!-- Analysis Complete -->
    <AnalysisCompleteCard v-if="currentStep === 'completed'" />
  </div>
</template>
