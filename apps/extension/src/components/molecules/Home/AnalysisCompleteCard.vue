<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import type { IAnalysisResult, IHeadResult, Verdict } from '@/types'
import { AlertTriangle, CheckCircle, HelpCircle } from 'lucide-vue-next'
import { Separator } from 'reka-ui'

defineProps<{ result: IAnalysisResult }>()
defineEmits<{ (e: 'reset'): void }>()

const VERDICTS: Record<Verdict, { label: string; icon: typeof CheckCircle; color: string }> = {
  likely_ai: { label: 'Likely AI-generated', icon: AlertTriangle, color: 'text-red-600' },
  inconclusive: { label: 'Inconclusive', icon: HelpCircle, color: 'text-amber-600' },
  no_evidence: { label: 'No evidence of AI found', icon: CheckCircle, color: 'text-green-600' },
}

const HEAD_LABELS: Record<string, string> = {
  face: 'Faces',
  scene: 'Whole frame',
  temporal: 'Motion',
}

const REASONS: Record<string, string> = {
  no_faces: 'no faces found',
  frames_too_small: 'frames too small',
  no_usable_bursts: 'no usable motion bursts',
  uncalibrated: 'measured, not yet calibrated',
}

const percent = (p: number | null) => (p === null ? '—' : `${Math.round(p * 100)}%`)

const headStatus = (head: IHeadResult) => {
  if (head.score !== null) return `${percent(head.score)} (${head.frames_scored} frames)`
  const reason = head.reason ?? ''
  return REASONS[reason] ?? (reason.startsWith('failed_to_load') ? 'failed to load' : reason)
}
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <component
          :is="VERDICTS[result.verdict].icon"
          class="h-5 w-5"
          :class="VERDICTS[result.verdict].color"
        />
        Analysis Complete
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="text-center p-6 bg-muted rounded-lg">
        <div class="text-lg mb-2" :class="VERDICTS[result.verdict].color">
          {{ VERDICTS[result.verdict].label }}
        </div>
        <div class="text-3xl font-bold mb-2">{{ percent(result.probability) }}</div>
        <p class="text-sm text-muted-foreground">
          Estimated chance of AI generation from {{ result.quality.usable_frames }} usable frames
        </p>
      </div>

      <div class="space-y-1 text-sm">
        <div v-for="head in result.heads" :key="head.name" class="flex justify-between gap-2">
          <span>{{ HEAD_LABELS[head.name] ?? head.name }}</span>
          <span class="text-muted-foreground text-right">{{ headStatus(head) }}</span>
        </div>
      </div>

      <Separator />

      <div class="space-y-2 text-xs text-muted-foreground">
        <p v-if="result.quality.flags.length">
          Input issues: {{ result.quality.flags.join(', ').replace(/_/g, ' ') }}
        </p>
        <p v-if="!result.calibrated">
          Scores are not yet calibrated on real-world video. Treat this as a hint, not proof.
        </p>
        <p>Processed in {{ (result.processing_time_ms / 1000).toFixed(1) }}s</p>
      </div>

      <Button class="w-full" variant="outline" @click.capture="$emit('reset')">
        Analyze Another Video
      </Button>
    </CardContent>
  </Card>
</template>
