<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

const GoogleIcon = defineAsyncComponent(() => import('@/components/atoms/icons/Google-icon.vue'))

defineProps<{
  text: string
  disabled: boolean
}>()
</script>
<template>
  <button
    class="flex items-center justify-center gap-[8px] p-[8px] rounded-xl bg-background cursor-pointer hover:bg-muted"
  >
    <GoogleIcon class="w-[16px] h-[16px]" />
    {{ text }}
  </button>
</template>
