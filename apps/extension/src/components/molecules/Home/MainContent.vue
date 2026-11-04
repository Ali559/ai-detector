<script setup lang="ts">
import IdleCard from './IdleCard.vue'
import ExtractingCard from './ExtractingCard.vue'
import ExtractedCard from './ExtractedCard.vue'
import AnalysisInProgressCard from './AnalysisInProgressCard.vue'
import AnalysisCompleteCard from './AnalysisCompleteCard.vue'
import type {
  IAnalysisResult,
  IExtractionResponse,
  IVideoFrame,
  IVideoMeta,
  ProcessState,
} from '@/types'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { MailWarning } from 'lucide-vue-next'
import AlertComponent from '@/components/atoms/AlertComponent.vue'

const currentStep = ref<ProcessState>('idle')
const frames = ref<IVideoFrame[]>([])
const meta = ref<IVideoMeta | null>(null)
const result = ref<IAnalysisResult | null>(null)
const err = ref<string>('')

const onMessage = (message: IExtractionResponse) => {
  if (message.type === 'error') {
    err.value = message.error || 'Something went wrong'
  }
  if (message.type === 'extracted') {
    currentStep.value = 'extracting'
    if (message.data) frames.value.push(message.data)
  }
  if (message.type === 'extraction-completed') {
    meta.value = message.meta ?? null
    currentStep.value = 'extracted'
  }
}

onMounted(() => {
  browser.runtime.onMessage.addListener(onMessage)
})

onBeforeUnmount(() => {
  browser.runtime.onMessage.removeListener(onMessage)
})

const reset = () => {
  frames.value = []
  meta.value = null
  result.value = null
  err.value = ''
  currentStep.value = 'idle'
}

const captureFrames = async (frameCount: number) => {
  err.value = ''
  try {
    await browser.runtime.sendMessage({
      type: 'start',
      frameCount,
    })
  } catch (error: unknown) {
    err.value = JSON.stringify(error)
  }
}

const onAnalysisComplete = (analysis: IAnalysisResult) => {
  result.value = analysis
  currentStep.value = 'completed'
}

const onAnalysisFailed = (message: string) => {
  err.value = message
  currentStep.value = 'extracted'
}
</script>
<template>
  <div class="flex-1 p-4 overflow-y-auto space-y-4">
    <AlertComponent
      v-if="err"
      :description="err"
      :title="currentStep === 'extracted' ? 'Error Analyzing Frames' : 'Error Capturing Frames'"
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
      :meta="meta"
      @reset="reset"
      @analyze="
        () => {
          err = ''
          currentStep = 'analyzing'
        }
      "
    />

    <!-- Analysis in Progress -->
    <AnalysisInProgressCard
      v-if="currentStep === 'analyzing'"
      :frames="frames"
      :meta="meta"
      @analysis-complete="onAnalysisComplete"
      @analysis-failed="onAnalysisFailed"
    />

    <!-- Analysis Complete -->
    <AnalysisCompleteCard
      v-if="currentStep === 'completed' && result"
      :result="result"
      @reset="reset"
    />
  </div>
</template>
