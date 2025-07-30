<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import type { IUser } from '@/types'
import { LogOut } from 'lucide-vue-next'
interface Props {
  user: IUser
}
defineProps<Props>()

// methods
const handleLogout = () => localStorage.removeItem('token')
</script>
<template>
  <section className="p-[16px] border-b border-border">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-[12px]">
        <!-- Avatar -->
        <div class="bg-muted flex items-center justify-center rounded-full w-[32px] h-[32px]">
          {{ user.name.charAt(0) }}
        </div>
        <div>
          <p className="text-sm font-medium">{{ user.name }}</p>
          <p className="text-xs text-muted-foreground">{{ user.email }}</p>
        </div>
      </div>
      <Button variant="ghost" size="sm" @click.capture="handleLogout">
        <LogOut className="h-4 w-4" />
      </Button>
    </div>
    <h2>AI Video Analyzer</h2>
  </section>
</template>
