<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import type { IUser } from '@/types'
import { LogOut } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
interface Props {
  user: IUser
}
const props = defineProps<Props>()
const router = useRouter()
// methods
const handleLogout = () => {
  localStorage.removeItem('token')
  router.push('/auth')
}
</script>
<template>
  <div class="p-4 border-b border-border">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-3">
        <div class="bg-border rounded-full w-8 h-8 flex items-center justify-center">
          {{ props.user.name.charAt(0) }}
        </div>
        <div>
          <p class="text-sm font-medium">{{ props.user.name }}</p>
          <p class="text-xs text-muted-foreground">{{ props.user.email }}</p>
        </div>
      </div>
      <Button variant="ghost" size="sm" @click.capture="handleLogout">
        <LogOut class="h-4 w-4" />
      </Button>
    </div>
    <h2>AI Video Analyzer</h2>
  </div>
</template>
