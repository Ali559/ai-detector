<script setup lang="ts">
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import { analyzeFrames } from '@/lib/analysis'
import type { IAnalysisResult, IVideoFrame, IVideoMeta } from '@/types'
import { Loader2 } from 'lucide-vue-next'
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps<{
  frames: IVideoFrame[]
  meta: IVideoMeta | null
}>()

const emit = defineEmits<{
  (e: 'analysis-complete', result: IAnalysisResult): void
  (e: 'analysis-failed', error: string): void
}>()

const elapsed = ref(0)
const controller = new AbortController()
let timer: ReturnType<typeof setInterval>

onMounted(async () => {
  timer = setInterval(() => elapsed.value++, 1000)
  try {
    emit('analysis-complete', await analyzeFrames(props.frames, props.meta, controller.signal))
  } catch (error) {
    if (!controller.signal.aborted) emit('analysis-failed', (error as Error).message)
  } finally {
    clearInterval(timer)
  }
})

onBeforeUnmount(() => {
  clearInterval(timer)
  controller.abort()
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Analyzing Frames...</CardTitle>
      <CardDescription>
        Checking faces, whole frames and motion. The first run can take a while.
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex items-center gap-2 text-sm">
        <Loader2 class="h-4 w-4 animate-spin" />
        <span>{{ elapsed }}s elapsed</span>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <img
          v-for="frame in frames.filter((f) => f.kind === 'sparse')"
          :key="frame.frameNumber"
          :src="frame.data"
          alt="frame"
          class="rounded-xl"
        />
      </div>
    </CardContent>
  </Card>
</template>
