<script setup lang="ts">
import GoogleIcon from '@/components/atoms/icons/Google-icon.vue'
import LineWithOr from '@/components/atoms/LineWithOr.vue'
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLoading = ref<boolean>(false)
const handleLogin = () => {
  isLoading.value = true
  localStorage.setItem('token', 'token')
  router.push('/')
}
</script>

<template>
  <Tabs default-value="login" class="w-full">
    <!-- Tabs -->
    <TabsList class="grid w-full grid-cols-2">
      <TabsTrigger value="login"> Login </TabsTrigger>
      <TabsTrigger value="signup"> Sign Up </TabsTrigger>
    </TabsList>

    <!-- Signup tab -->
    <TabsContent value="signup">
      <Card>
        <CardHeader class="pb-4">
          <CardTitle>Create account </CardTitle>
          <CardDescription> Get started with AI video analysis </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <Button variant="outline" class="w-full">
            <GoogleIcon class="w-4 h-4" />
            Sign up with Google
          </Button>

          <LineWithOr />

          <div class="space-y-1">
            <Label for="name">Full Name</Label>
            <Input id="name" />
          </div>
          <div class="space-y-1">
            <Label for="new-email">Username</Label>
            <Input id="new-email" type="email" />
          </div>
          <div class="space-y-1">
            <Label for="new-passwordl">Password</Label>
            <Input id="new-password" type="password" />
          </div>
        </CardContent>
        <CardFooter>
          <Button class="w-full">{{ isLoading ? 'Creating Account...' : 'Create Account' }}</Button>
        </CardFooter>
      </Card>
    </TabsContent>

    <!-- Login tab -->
    <TabsContent value="login">
      <Card>
        <CardHeader class="pb-4">
          <CardTitle>Welcome back</CardTitle>
          <CardDescription> Sign in to your account </CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <Button variant="outline" class="w-full">
            <GoogleIcon class="w-4 h-4" />
            Continue with Google
          </Button>
          <LineWithOr />
          <div class="space-y-1">
            <Label for="login-email">Email</Label>
            <Input id="login-email" type="email" />
          </div>
          <div class="space-y-1">
            <Label for="login-password">Password</Label>
            <Input id="login-password" type="password" />
          </div>
        </CardContent>
        <CardFooter>
          <Button class="w-full" @click.capture="handleLogin">{{
            isLoading ? 'Signing in...' : 'Sign in'
          }}</Button>
        </CardFooter>
      </Card>
    </TabsContent>
  </Tabs>
</template>
