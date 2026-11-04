<script setup lang="ts">
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import type { IVideoFrame } from '@/types'
import { Loader2 } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  frames: IVideoFrame[]
}>()
const sparse = computed(() => props.frames.filter((f) => f.kind === 'sparse'))
const burstFrames = computed(() => props.frames.length - sparse.value.length)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Extracting Frames...</CardTitle>
      <CardDescription>
        The video will seek and play briefly, then return to where you were
      </CardDescription>
    </CardHeader>
    <CardContent>
      <div class="flex items-center gap-2 mb-4">
        <Loader2 class="h-4 w-4 animate-spin" />
        <span>{{ sparse.length }} frames, {{ burstFrames }} burst frames</span>
      </div>
      <div class="grid grid-cols-2 gap-2">
        <img
          v-for="frame in sparse"
          :key="frame.frameNumber"
          :src="frame.data"
          alt="frame"
          class="rounded-xl"
        />
      </div>
    </CardContent>
  </Card>
</template>
