<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <CheckCircle class="h-5 w-5 text-green-600" />
        Frames Extracted
      </CardTitle>
      <CardDescription>
        {frameCount} frame{parseInt(frameCount) !== 1 ? 's' : ''} successfully captured
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="grid grid-cols-2 gap-2"></div>
      <div class="flex gap-2">
        <Button class="flex-1">
          <Image class="h-4 w-4 mr-2" />
          Analyze
        </Button>
        <Button variant="outline"> Reset </Button>
      </div>
    </CardContent>
  </Card>
</template>
