<script setup lang="ts">
import Alert from '../ui/alert/Alert.vue'
import AlertTitle from '../ui/alert/AlertTitle.vue'
import AlertDescription from '../ui/alert/AlertDescription.vue'
import type { Component } from 'vue'

defineProps<{
  title: string
  description: string
  icon: Component
}>()
</script>
<template>
  <Alert>
    <component :is="icon" />
    <AlertTitle>Heads up!</AlertTitle>
    <AlertDescription> You can add components to your app using the cli. </AlertDescription>
  </Alert>
</template>
