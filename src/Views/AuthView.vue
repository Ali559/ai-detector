<script setup lang="ts">
import type { ITab } from '@/types'
import { defineAsyncComponent, ref } from 'vue'
const TabComponent = defineAsyncComponent(() => import('@/components/atoms/TabComponent.vue'))
const LoginComponent = defineAsyncComponent(
  () => import('@/components/molecules/Auth/LoginComponent.vue'),
)
const SignupComponent = defineAsyncComponent(
  () => import('@/components/molecules/Auth/SignupComponent.vue'),
)
const tabs: ITab[] = [
  {
    id: 'login',
    name: 'Login',
  },
  {
    id: 'signup',
    name: 'Sign Up',
  },
]

const selectedTab = ref<ITab>(tabs[0])
</script>
<template>
  <div class="@container p-[8px]">
    <!-- Header Section -->
    <div class="mb-6 p-[16px] text-center">
      <h1 class="text-[1.5rem]">AI Video Analyzer</h1>
      <p className="text-muted-foreground mt-2">Detect AI-generated content in videos</p>
    </div>

    <!-- Tabs -->
    <TabComponent :tabs="tabs" @tab-click="selectedTab = $event" :selected-tab="selectedTab" />

    <!-- Tab Content -->
    <div class="mt-[4px]">
      <LoginComponent v-if="selectedTab.id === 'login'" />
      <SignupComponent v-else />
    </div>
  </div>
</template>
