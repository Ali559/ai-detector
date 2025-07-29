<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue'

const GoogleIcon = defineAsyncComponent(() => import('@/components/atoms/icons/Google-icon.vue'))
const isLoading = ref<boolean>(false)
const password = ref<string>('')
const email = ref<string>('')
</script>
<template>
  <div class="bg-card text-card-foreground flex flex-col gap-[16px] rounded-xl border p-[16px]">
    <!-- Header -->
    <div class="text-start">
      <h4 class="leading-[0px]">Welcome back</h4>
      <p class="text-muted-foreground">Sign in to your account</p>
    </div>

    <button class="flex items-center justify-center gap-[8px] p-[8px] rounded-xl bg-background cursor-pointer">
      <GoogleIcon class="w-[16px] h-[16px]" />
      Continue with Google
    </button>

    <!-- line with or in between -->
    <div class="flex items-center justify-center gap-[8px]">
      <div class="w-full h-[1px] bg-muted"></div>
      <p class="text-muted-foreground bg-background px-2">or</p>
      <div class="w-full h-[1px] bg-muted"></div>
    </div>

    <!-- Form -->
    <form @submit="(e) => e.preventDefault()" class="flex flex-col gap-[16px]">
      <!-- Email inputgroup -->
      <div className="flex flex-col gap-[4px]">
        <Label htmlFor="signup-email">Email</Label>
        <Input
          class="bg-muted outline-0 border-0 focus:outline-4 focus:outline-muted-foreground p-[8px] rounded-lg"
          id="signup-email"
          type="email"
          placeholder="Enter your email"
          v-model="email"
          required
        />
      </div>
      <!-- Password inputgroup -->
      <div className="flex flex-col gap-[8px]">
        <Label htmlFor="signup-password">Password</Label>
        <Input
          class="bg-muted outline-0 border-0 focus:outline-4 focus:outline-muted-foreground p-[8px] rounded-lg"
          id="signup-password"
          type="password"
          placeholder="Enter your password"
          v-model="password"
          required
        />
      </div>
      <Button
        type="submit"
        className="w-full"
        :disabled="isLoading"
        class="w-full rounded-lg p-[8px] bg-[#000] text-background disabled:bg-muted disabled:text-muted font-bold"
      >
        {{ isLoading ? 'Signing in...' : 'Login' }}
      </Button>
    </form>
  </div>
</template>
