<script setup lang="ts">
defineProps<{
  text: string
  disabled?: boolean
}>()
const emit = defineEmits(['button-clicked'])
</script>
<template>
  <button
    :disabled="disabled"
    @click="emit('button-clicked')"
    class="w-full rounded-lg p-[8px] bg-[#000] text-background cursor-pointer disabled:bg-foreground/70 disabled:text-muted"
  >
    {{ text }}
  </button>
</template>
