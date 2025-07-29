<script setup lang="ts">
import type { InuptType } from '@/types'
import { ref } from 'vue'
defineProps<InuptType>()
const value = ref<string>('')
</script>
<template>
  <div className="flex flex-col gap-[4px]">
    <Label htmlFor="signup-email">{{label}}</Label>
    <Input
      class="bg-muted outline-0 border-0 transition-all duration-300 ease-in-out focus:outline-2 focus:outline-muted-foreground p-[8px] rounded-lg"
      id="signup-email"
      type="email"
      placeholder="Enter your email"
      v-model="value"
      required
    />
  </div>
</template>
