<script setup lang="ts">
import IdleCard from './IdleCard.vue'
import ExtractingCard from './ExtractingCard.vue'
import ExtractedCard from './ExtractedCard.vue'
import AnalysisInProgressCard from './AnalysisInProgressCard.vue'
import AnalysisCompleteCard from './AnalysisCompleteCard.vue'
import type { ProcessState } from '@/types'
import { ref } from 'vue'
// import { useFramesStore } from '@/store/framesStore'
import { FileWarningIcon } from 'lucide-vue-next'
import AlertComponent from '@/components/atoms/AlertComponent.vue'

const currentStep = ref<ProcessState>('idle')

// const { setFrames, addFrame } = useFramesStore()
const error = ref<string | undefined>('')
// const captureFrames = async (frameCount: number) => {
//   const result: CaptureResult = await browser.runtime.sendMessage({
//     action: 'captureFrames',
//     frameCount: frameCount,
//   })

//   browser.runtime.onMessage.addListener((message) => {
//     if(message.action === 'frameCaptured') {
//       currentStep.value = 'extracting'

//       addFrame(message.frae)
//       frameNumber: i + 1,
//             totalFrames: frameCount,
//             timestamp: video.currentTime
//     }
//   })
// }
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
    <IdleCard v-if="currentStep === 'idle'" />

    <!-- Extracting Frames... -->
    <ExtractingCard v-if="currentStep === 'extracting'" />

    <!-- Extracted Frames -->
    <ExtractedCard v-if="currentStep === 'extracted'" />

    <!-- Analysis in Progress -->
    <AnalysisInProgressCard v-if="currentStep === 'analyzing'" />

    <!-- Analysis Complete -->
    <AnalysisCompleteCard v-if="currentStep === 'completed'" />
  </div>
</template>
