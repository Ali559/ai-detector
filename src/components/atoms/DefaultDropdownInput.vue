<!-- FrameSelect.vue -->
<script setup lang="ts">
import { ref } from 'vue'

const {frames} = defineProps<{ frames: string[] }>()
const selected = ref(frames[8]) // Default: 9 frames
const isOpen = ref(false)

function toggle() {
  isOpen.value = !isOpen.value
}

function selectFrame(frame: string) {
  selected.value = frame
  isOpen.value = false
}
</script>

<template>
  <div class="relative w-full h-max">
    <!-- Button -->
    <button
      @click="toggle"
      class="w-full bg-muted text-left px-2 py-1.5 rounded-md border border-input text-sm flex justify-between items-center"
    >
      {{ selected }}
      <svg
        class="h-4 w-4 ml-2 text-muted-foreground"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Dropdown -->
    <ul
      v-if="isOpen"
      class="absolute z-50 mt-1 w-full bg-popover border border-border rounded-md shadow-lg max-h-60 overflow-auto text-sm"
    >
      <li
        v-for="frame in frames"
        :key="frame"
        @click="selectFrame(frame)"
        :class="[
          'px-3 py-2 cursor-pointer hover:bg-muted ',
          selected === frame ? 'bg-muted text-primary' : '',
        ]"
      >
        {{ frame }}
        <span v-if="selected === frame">✓</span>
      </li>
    </ul>
  </div>
</template>
