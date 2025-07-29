<script setup lang="ts">
import type { ITab } from '@/types'

defineProps<{
  tabs: ITab[]
  selectedTab: ITab
}>()

const emit = defineEmits<{
  (e: 'tabClick', tab: ITab): void
}>()
</script>
<template>
  <div
    class="bg-muted text-muted-foreground h-[30px] w-full flex items-center justify-center rounded-xl p-[3px]"
  >
    <button
      :class="selectedTab.id === tab.id ? 'bg-background' : ''"
      class="text-sm font-semibold text-center h-full w-full rounded-full cursor-pointer border-none outline-none transition-colors duration-300 ease-in-out"
      v-for="tab in tabs"
      :key="tab.id"
      @click="emit('tabClick', tab)"
    >
      {{ tab.name }}
    </button>
  </div>
</template>
