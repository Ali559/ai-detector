<script setup lang="ts">
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { signIn, signUp } from '@/lib/api'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

// Google sign-in is hidden until the API has an OAuth provider configured.

const router = useRouter()
const isLoading = ref<boolean>(false)
const error = ref<string>('')
const login = reactive({ email: '', password: '' })
const signup = reactive({ name: '', email: '', password: '' })

const submit = async (action: () => Promise<unknown>) => {
  error.value = ''
  isLoading.value = true
  try {
    await action()
    router.push('/')
  } catch (e) {
    error.value = (e as Error).message || 'Something went wrong'
  } finally {
    isLoading.value = false
  }
}

const handleLogin = () => submit(() => signIn(login.email, login.password))
const handleSignup = () => submit(() => signUp(signup.name, signup.email, signup.password))
</script>

<template>
  <Tabs default-value="login" class="w-full" @update:model-value="error = ''">
    <!-- Tabs -->
    <TabsList class="grid w-full grid-cols-2">
      <TabsTrigger value="login"> Login </TabsTrigger>
      <TabsTrigger value="signup"> Sign Up </TabsTrigger>
    </TabsList>

    <!-- Signup tab -->
    <TabsContent value="signup">
      <form @submit.prevent="handleSignup">
        <Card>
          <CardHeader class="pb-4">
            <CardTitle>Create account </CardTitle>
            <CardDescription> Get started with AI video analysis </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-1">
              <Label for="name">Full Name</Label>
              <Input id="name" v-model="signup.name" required minlength="3" />
            </div>
            <div class="space-y-1">
              <Label for="new-email">Email</Label>
              <Input id="new-email" v-model="signup.email" type="email" required />
            </div>
            <div class="space-y-1">
              <Label for="new-password">Password</Label>
              <Input
                id="new-password"
                v-model="signup.password"
                type="password"
                required
                minlength="8"
                maxlength="48"
              />
            </div>
            <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          </CardContent>
          <CardFooter>
            <Button class="w-full" type="submit" :disabled="isLoading">
              {{ isLoading ? 'Creating Account...' : 'Create Account' }}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </TabsContent>

    <!-- Login tab -->
    <TabsContent value="login">
      <form @submit.prevent="handleLogin">
        <Card>
          <CardHeader class="pb-4">
            <CardTitle>Welcome back</CardTitle>
            <CardDescription> Sign in to your account </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-1">
              <Label for="login-email">Email</Label>
              <Input id="login-email" v-model="login.email" type="email" required />
            </div>
            <div class="space-y-1">
              <Label for="login-password">Password</Label>
              <Input id="login-password" v-model="login.password" type="password" required />
            </div>
            <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          </CardContent>
          <CardFooter>
            <Button class="w-full" type="submit" :disabled="isLoading">
              {{ isLoading ? 'Signing in...' : 'Sign in' }}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </TabsContent>
  </Tabs>
</template>
