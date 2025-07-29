<script setup lang="ts">
import type { InuptType } from '@/types'
import { defineAsyncComponent, ref } from 'vue'
const DefaultInputGroup = defineAsyncComponent(
  () => import('@/components/atoms/DefaultInputGroup.vue'),
)
const SSOButton = defineAsyncComponent(() => import('@/components/atoms/SSOButton.vue'))
const LineWithOr = defineAsyncComponent(() => import('@/components/atoms/LineWithOr.vue'))
const TopCard = defineAsyncComponent(() => import('@/components/atoms/TopCard.vue'))
const DefaultButton = defineAsyncComponent(() => import('@/components/atoms/DefaultButton.vue'))
// State
const isLoading = ref<boolean>(false)

// Data & essentials
const listOfInputs: InuptType[] = [
  {
    id: 'fullname',
    label: 'Full Name',
    placeHolder: 'Enter your full name',
    type: 'text',
  },
  {
    id: 'email',
    label: 'Email',
    placeHolder: 'Enter your email',
    type: 'email',
  },
  {
    id: 'password',
    label: 'Password',
    placeHolder: 'Create a password',
    type: 'password',
  },
]
</script>
<template>
  <div class="bg-card text-card-foreground flex flex-col gap-[8px] rounded-xl border p-[16px]">
    <!-- Top Card -->
    <TopCard title="Create account" description="Get started with AI video analysis" />

    <SSOButton text="Sign up with Google" :disabled="isLoading" />

    <!-- line with or in between -->
    <LineWithOr />

    <!-- Form -->
    <form @submit="(e) => e.preventDefault()" class="flex flex-col gap-[16px]">
      <!-- Input Groups -->
      <DefaultInputGroup v-for="(item, index) in listOfInputs" :key="index" v-bind="item" />

      <!-- Default Button -->
      <DefaultButton
        :disabled="isLoading"
        :text="isLoading ? 'Creating Account...' : 'Create Account'"
        @button-clicked="isLoading = true"
      />
    </form>
  </div>
</template>
