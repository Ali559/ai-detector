<script setup lang="ts">
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import type { IVideoFrame } from '@/types'
import { Loader2 } from 'lucide-vue-next'

defineProps<{
  frames: IVideoFrame[]
}>()
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Extracting Frames...</CardTitle>
      <CardDescription> Capturing frames from the video player </CardDescription>
    </CardHeader>
    <CardContent>
      <div class="flex items-center gap-2 mb-4">
        <Loader2 class="h-4 w-4 animate-spin" />
        <span>Extracting frame </span>
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
