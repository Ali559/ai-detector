<script setup lang="ts">
import Alert from '../ui/alert/Alert.vue'
import AlertTitle from '../ui/alert/AlertTitle.vue'
import AlertDescription from '../ui/alert/AlertDescription.vue'
import { onMounted, type Component } from 'vue'

defineProps<{
  title: string
  description: string
  icon: Component
}>()
onMounted(() => {
  setTimeout(() => {
    const alert = document.querySelector('[data-slot="alert"]')
    if (alert) {
      alert.remove()
    }
  }, 3000)
})
</script>
<template>
  <Alert>
    <component :is="icon" color="red" />
    <AlertTitle>{{ title }}</AlertTitle>
    <AlertDescription> {{ description }} </AlertDescription>
  </Alert>
</template>
