<script setup lang="ts">
import type { InuptType } from '@/types'
import { defineAsyncComponent, ref } from 'vue'
import { useRouter } from 'vue-router'
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
    id: 'email',
    label: 'Email',
    placeHolder: 'Enter your email',
    type: 'email',
  },
  {
    id: 'password',
    label: 'Password',
    placeHolder: 'Enter your password',
    type: 'password',
  },
]

// hooks
const router = useRouter()
// Methods
const handleSubmit = (e: Event) => {
  e.preventDefault()
  isLoading.value = true
  localStorage.setItem('token', 'token')
  router.push('/')
}
</script>
<template>
  <div class="bg-card text-card-foreground flex flex-col gap-[8px] rounded-xl border p-[16px]">
    <!-- Top Card -->
    <TopCard title="Welcome back" description="Sign in to your account" />

    <SSOButton text="Continue with Google" :disabled="isLoading" />

    <!-- line with or in between -->
    <LineWithOr />

    <!-- Form -->
    <form @submit="handleSubmit" class="flex flex-col gap-[16px]">
      <!-- Input Groups -->
      <DefaultInputGroup v-for="(item, index) in listOfInputs" :key="index" v-bind="item" />

      <!-- Default Button -->
      <DefaultButton
        :disabled="isLoading"
        :text="isLoading ? 'Signing in...' : 'Sign in'"
        @button-clicked="handleSubmit"
      />
    </form>
  </div>
</template>
