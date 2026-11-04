<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import type { IVideoFrame, IVideoMeta } from '@/types'
import { CheckCircle, Image } from 'lucide-vue-next'
import { computed } from 'vue'

const props = defineProps<{
  frames: IVideoFrame[]
  meta: IVideoMeta | null
}>()
const sparse = computed(() => props.frames.filter((f) => f.kind === 'sparse'))
const bursts = computed(
  () => new Set(props.frames.filter((f) => f.kind === 'burst').map((f) => f.burstIndex)).size,
)
const emit = defineEmits<{
  (e: 'reset'): void
  (e: 'analyze'): void
}>()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <CheckCircle class="h-5 w-5 text-green-600" />
        Frames Extracted
      </CardTitle>
      <CardDescription>
        {{ sparse.length }} frame{{ sparse.length === 1 ? '' : 's' }} and {{ bursts }} motion
        burst{{ bursts === 1 ? '' : 's' }}
        <template v-if="meta"> at {{ meta.width }}×{{ meta.height }}</template>
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <p v-if="meta?.captureMethod === 'tab_capture'" class="text-sm text-muted-foreground">
        This site blocks direct frame access, so frames were screenshotted from the tab and motion
        bursts were skipped. Results will be less reliable.
      </p>
      <div class="grid grid-cols-2 gap-2 overflow-y-auto">
        <img
          v-for="frame in sparse"
          :key="frame.frameNumber"
          :src="frame.data"
          alt="frame"
          class="rounded-xl"
        />
      </div>
      <div class="flex items-center gap-2">
        <Button class="flex-1" @click.capture="emit('analyze')"
          ><Image class="h-4 w-4" /> Analyze
        </Button>
        <Button variant="outline" @click.capture="emit('reset')"> Reset </Button>
      </div>
    </CardContent>
  </Card>
</template>
