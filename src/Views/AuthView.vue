<script setup lang="ts">
import type { ITab } from '@/types'
import { defineAsyncComponent, ref } from 'vue'
const TabComponent = defineAsyncComponent(() => import('@/components/atoms/TabComponent.vue'))
const LoginComponent = defineAsyncComponent(
  () => import('@/components/molecules/LoginComponent.vue'),
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
  <div class="@container">
    <!-- Header Section -->
    <div class="text-center mb-6 p-[16px]">
      <h1>AI Video Analyzer</h1>
      <p className="text-muted-foreground mt-2">Detect AI-generated content in videos</p>
    </div>

    <!-- Tabs -->
    <TabComponent :tabs="tabs" @tab-click="selectedTab = $event" :selected-tab="selectedTab" />

    <!-- Tab Content -->
    <div class="mt-[4px]">
      <LoginComponent v-if="selectedTab.id === 'login'" />
    </div>
  </div>
</template>
