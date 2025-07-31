<script setup lang="ts">
import type { IUser } from '@/types'
import { defineAsyncComponent } from 'vue'
const HeaderComponent = defineAsyncComponent(
  () => import('@/components/molecules/Home/HeaderComponent.vue'),
)
const MainContent = defineAsyncComponent(
  () => import('@/components/molecules/Home/MainContent.vue'),
)
const userData: IUser = {
  id: 'a753d5ca-4f93-4d88-93fe-49100b328c2d',
  name: 'Ali Barznji',
  email: 'biz@alibarznji.dev',
}
</script>
<template>
  <div class="felx flex-col h-full">
    <HeaderComponent :user="userData" />

    <MainContent />
  </div>
</template>
