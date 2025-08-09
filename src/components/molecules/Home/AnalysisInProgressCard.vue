<script setup lang="ts">
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Progress from '@/components/ui/progress/Progress.vue'
import type { IVideoFrame } from '@/types'
import { onMounted, ref, watch } from 'vue'

defineProps<{
  frames: IVideoFrame[]
}>()
const analysisProgress = ref<number>(0)
const startAnalysis = () => {
  setInterval(() => {
    analysisProgress.value += 10
  }, 1000)
}
onMounted(() => {
  startAnalysis()
})

const emit = defineEmits<{
  (e: 'analysis-complete'): void
}>()

watch(analysisProgress, () => {
  if (analysisProgress.value === 100) emit('analysis-complete')
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Analyzing Frames...</CardTitle>
      <CardDescription> Processing frames with AI detection model </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="space-y-2">
        <div class="flex justify-between text-sm">
          <span>Analysis Progress</span>
          <span>{{ analysisProgress }}%</span>
        </div>
        <Progress v-model="analysisProgress" />
      </div>
      <div class="grid grid-cols-2 gap-2">
        <img
          v-for="(frame, index) in frames"
          :key="index"
          :src="frame.data"
          alt="frame"
          class="rounded-xl"
        />
      </div>
    </CardContent>
  </Card>
</template>
