<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ progressValue: number }>()
const svgSize = 100
const strokeWidth = 10
const radius = svgSize / 2 - strokeWidth / 2
const circumference = 2 * Math.PI * radius

const progressCircleStyle = computed(() => {
  const offset = circumference - (props.progressValue / 100) * circumference
  return {
    strokeDasharray: `${circumference} ${circumference}`,
    strokeDashoffset: offset,
    transform: 'rotate(-90deg)',
    transformOrigin: '50% 50%',
    transition: 'stroke-dashoffset 0.5s ease-in-out',
  }
})
</script>

<template>
  <svg class="max-w-16 max-h-16" :viewBox="`0 0 ${svgSize} ${svgSize}`">
    <circle
      class="text-white stroke-current"
      :stroke-width="strokeWidth"
      :cx="svgSize / 2"
      :cy="svgSize / 2"
      :r="radius"
      fill="transparent"
    ></circle>

    <circle
      class="text-indigo-500 stroke-current stroke-linecap-round"
      :stroke-width="strokeWidth"
      :cx="svgSize / 2"
      :cy="svgSize / 2"
      :r="radius"
      fill="transparent"
      :style="progressCircleStyle"
      role="progressbar"
      :aria-valuenow="progressValue"
      aria-valuemin="0"
      aria-valuemax="100"
    ></circle>
  </svg>
</template>
