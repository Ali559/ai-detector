<script setup lang="ts">
import TabCards from '@/components/molecules/Auth/TabCards.vue'
// import type { ITab } from '@/types'
// const tabs: ITab[] = [
//   {
//     id: 'login',
//     name: 'Login',
//   },
//   {
//     id: 'signup',
//     name: 'Sign Up',
//   },
// ]

// const selectedTab = ref<ITab>(tabs[0])
</script>
<template>
  <div class="h-full flex flex-col">
    <div class="p-6">
      <!-- Header Section -->
      <div className="text-center mb-6">
        <h1>AI Video Analyzer</h1>
        <p className="text-muted-foreground mt-2">Detect AI-generated content in videos</p>
      </div>

      <TabCards />
    </div>
  </div>
</template>
