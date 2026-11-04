<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import type { IVideoFrame } from '@/types'
import { Image } from 'lucide-vue-next'
defineProps<{
  frames: IVideoFrame[]
}>()
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
        {{ `${frames.length} Frame${frames.length === 1 ? '' : 's'} Successfully Captured` }}
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="grid grid-cols-2 gap-2 overflow-y-auto">
        <img
          v-for="(frame, index) in frames"
          :key="index"
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
