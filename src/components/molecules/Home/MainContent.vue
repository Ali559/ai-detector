<script setup lang="ts">
import DefaultDropdownInput from '@/components/atoms/DefaultDropdownInput.vue'
import type { IStep } from '@/types'

interface Props {
  currentStep: IStep
}
defineProps<Props>()

const dropdownItems = [
  '1 frame',
  '2 frames',
  '3 frames',
  '4 frames',
  '5 frames',
  '6 frames',
  '7 frames',
  '8 frames',
  '9 frames',
  '10 frames',
]
</script>
<template>
  <section class="p-[16px]">
    <div class="border border-border rounded-[8px] p-[16px]">
      <h4 class="leading-none">{{ currentStep.title }}</h4>
      <p v-if="currentStep.description" class="text-muted-foreground leading-none">
        {{ currentStep.description }}
      </p>

      <div class="mt-[16px]">
        <DefaultDropdownInput :frames='dropdownItems' />
      </div>
    </div>
  </section>
</template>
