<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>
<template>
  <div class="text-start">
    <h4 class="leading-[0px]">{{ title }}</h4>
    <p class="text-muted-foreground">{{ description }}</p>
  </div>
</template>
