<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Select from '@/components/ui/select/Select.vue'
import SelectContent from '@/components/ui/select/SelectContent.vue'
import SelectItem from '@/components/ui/select/SelectItem.vue'
import SelectTrigger from '@/components/ui/select/SelectTrigger.vue'
import SelectValue from '@/components/ui/select/SelectValue.vue'
import { Play } from 'lucide-vue-next'
import { ref } from 'vue'

const FRAME_COUNTS = ['8', '16', '24', '32'] as const
const frameCount = ref<(typeof FRAME_COUNTS)[number]>('16')

const emit = defineEmits<{
  (e: 'captureFrames', frameCount: number): void
}>()
</script>
<template>
  <Card>
    <CardHeader>
      <CardTitle>Extract Video Frames</CardTitle>
      <CardDescription>
        Samples frames across the playing video, plus two short bursts of consecutive frames to
        check motion
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4 p-4">
      <div class="space-y-2">
        <label class="block">Frames across the video</label>
        <Select v-model="frameCount">
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Select number of frames" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="count in FRAME_COUNTS" :key="count" :value="count"
              >{{ count }} frames</SelectItem
            >
          </SelectContent>
        </Select>
      </div>
      <Button class="w-full" @click.capture="emit('captureFrames', Number(frameCount))">
        <Play class="h-4 w-4 mr-2" />
        Start Extraction
      </Button>
    </CardContent>
  </Card>
</template>
