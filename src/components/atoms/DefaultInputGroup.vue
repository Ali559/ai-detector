<script setup lang="ts">
import type { InuptType } from '@/types'
import { ref } from 'vue'
defineProps<InuptType>()
const value = ref<string>('')
</script>
<template>
  <div className="flex flex-col gap-[4px]">
    <label :htmlFor="id">{{ label }}</label>
    <input
      class="bg-muted outline-0 border-0 transition-all duration-300 ease-in-out focus:outline-2 focus:outline-muted-foreground p-[8px] rounded-lg"
      :id="id"
      :type="type"
      :placeholder="placeHolder"
      v-model="value"
      required
    />
  </div>
</template>
