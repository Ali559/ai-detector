<script setup lang="ts">
import IdleCard from './IdleCard.vue'
import ExtractingCard from './ExtractingCard.vue'
import ExtractedCard from './ExtractedCard.vue'
import AnalysisInProgressCard from './AnalysisInProgressCard.vue'
import AnalysisCompleteCard from './AnalysisCompleteCard.vue'
import type { ProcessState } from '@/types'
interface Props {
  currentStep: ProcessState
}
defineProps<Props>()
</script>
<template>
  <div class="flex-1 p-4 overflow-y-auto space-y-4">
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
