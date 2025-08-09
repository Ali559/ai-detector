<script setup lang="ts">
import IdleCard from './IdleCard.vue'
import ExtractingCard from './ExtractingCard.vue'
import ExtractedCard from './ExtractedCard.vue'
import AnalysisInProgressCard from './AnalysisInProgressCard.vue'
import AnalysisCompleteCard from './AnalysisCompleteCard.vue'
import type { IExtractionResponse, IVideoFrame, ProcessState } from '@/types'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { MailWarning } from 'lucide-vue-next'
import AlertComponent from '@/components/atoms/AlertComponent.vue'

const currentStep = ref<ProcessState>('idle')
const frames = ref<IVideoFrame[]>([])
// const { error, setError } = useErrorStore()
const err = ref<string>('')
const handleFrameExtraction = (frameExtractionResult: IExtractionResponse) => {
  if (frameExtractionResult.type !== 'extracted') return (err.value = 'Something went wrong')
  if (!frameExtractionResult.data) return (err.value = 'No frames extracted')

  frames.value.push(frameExtractionResult.data)
}
const onMessage = (message: IExtractionResponse) => {
  if (message.type === 'error') {
    err.value = message.error || 'Something went wrong'
  }
  if (message.type === 'extracted') {
    currentStep.value = 'extracting'
    handleFrameExtraction(message)
  }
  if (message.type === 'extraction-completed') currentStep.value = 'extracted'
}

onMounted(() => {
  browser.runtime.onMessage.addListener(onMessage)
})

onBeforeUnmount(() => {
  browser.runtime.onMessage.removeListener(onMessage)
})

const captureFrames = async (frameCount: number) => {
  try {
    await browser.runtime.sendMessage({
      type: 'start',
      frameCount,
    })
  } catch (error: unknown) {
    err.value = JSON.stringify(error)
  }
}
</script>
<template>
  <div class="flex-1 p-4 overflow-y-auto space-y-4">
    <AlertComponent
      v-if="err"
      :description="err"
      title="Error Capturing Frames"
      :icon="MailWarning"
    />
    <!-- Extract Video Frames -->
    <IdleCard v-if="currentStep === 'idle'" @capture-frames="captureFrames" />

    <!-- Extracting Frames... -->
    <ExtractingCard v-if="currentStep === 'extracting'" :frames="frames" />

    <!-- Extracted Frames -->
    <ExtractedCard
      v-if="currentStep === 'extracted'"
      :frames="frames"
      @reset="
        () => {
          frames = []
          currentStep = 'idle'
          console.log(frames.length)
        }
      "
    />

    <!-- Analysis in Progress -->
    <AnalysisInProgressCard v-if="currentStep === 'analyzing'" />

    <!-- Analysis Complete -->
    <AnalysisCompleteCard v-if="currentStep === 'completed'" />
  </div>
</template>
