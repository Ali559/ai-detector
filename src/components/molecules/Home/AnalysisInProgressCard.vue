<script setup lang="ts">
import Card from '@/components/ui/card/Card.vue';
import CardContent from '@/components/ui/card/CardContent.vue';
import CardDescription from '@/components/ui/card/CardDescription.vue';
import CardHeader from '@/components/ui/card/CardHeader.vue';
import CardTitle from '@/components/ui/card/CardTitle.vue';
import { Progress } from 'reka-ui/namespaced';

</script>

<template>
   <Card >
      <CardHeader>
        <CardTitle>Analyzing Frames...</CardTitle>
        <CardDescription> Processing frames with AI detection model </CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <div class="flex justify-between text-sm">
            <span>Analysis Progress</span>
            <span>{analysisProgress}%</span>
          </div>
          <Progress value="{analysisProgress}" />
        </div>
        <div class="grid grid-cols-2 gap-2"></div>
      </CardContent>
    </Card>
</template>
