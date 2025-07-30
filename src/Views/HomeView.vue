<script setup lang="ts">
import type { IStep, IUser } from '@/types'
import { defineAsyncComponent, ref } from 'vue'
const HeaderComponent = defineAsyncComponent(
  () => import('@/components/molecules/Home/HeaderComponent.vue'),
)
const MainContent = defineAsyncComponent(
  () => import('@/components/molecules/Home/MainContent.vue'),
)
const userData: IUser = {
  id: 'a753d5ca-4f93-4d88-93fe-49100b328c2d',
  name: 'Ali Barznji',
  email: 'biz@alibarznji.dev',
}

const steps: IStep[] = [
  {
    id: 'extract-video-frames',
    title: 'Extract Video Frames',
    description: "Select how many frames to extract from the active tab's video player",
  },
  {
    id: 'extracting-frames',
    title: 'Extracting Frames...',
    description: 'Capturing frames from the video player',
  },
  {
    id: 'frames-extracted',
    title: 'Frames Extracted',
    description: 'frames successfully captured',
  },
  {
    id: 'analyzing-frames',
    title: 'Analyzing Frames...',
    description: 'Processing frames with AI detection model',
  },
  {
    id: 'frames-analyzed',
    title: 'Analysis Complete',
  },
]

const currentStep = ref<IStep>(steps[0])
</script>
<template>
  <!-- Header Component  -->
  <HeaderComponent :user="userData" />

  <!-- Main Content -->
  <MainContent :current-step="currentStep" />
</template>
