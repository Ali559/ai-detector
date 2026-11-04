<script setup lang="ts">
import { ApiError, currentUser } from '@/lib/api'
import type { IUser } from '@/types'
import { defineAsyncComponent, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
const HeaderComponent = defineAsyncComponent(
  () => import('@/components/molecules/Home/HeaderComponent.vue'),
)
const MainContent = defineAsyncComponent(
  () => import('@/components/molecules/Home/MainContent.vue'),
)

const router = useRouter()
const user = ref<IUser | null>(null)

onMounted(async () => {
  try {
    user.value = await currentUser()
  } catch (error) {
    // An expired session clears the token; send the user back to sign in.
    if (error instanceof ApiError && error.status === 401) router.push('/auth')
  }
})
</script>
<template>
  <div class="flex flex-col h-full">
    <HeaderComponent v-if="user" :user="user" />

    <MainContent />
  </div>
</template>
