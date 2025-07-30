<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue';
import Card from '@/components/ui/card/Card.vue';
import CardContent from '@/components/ui/card/CardContent.vue';
import CardHeader from '@/components/ui/card/CardHeader.vue';
import CardTitle from '@/components/ui/card/CardTitle.vue';
import { AlertTriangle, CheckCircle } from 'lucide-vue-next';
import { Separator } from 'reka-ui';

</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        {analysisResult.isAI ? (
        <AlertTriangle class="h-5 w-5 text-red-600" />
        ) : (
        <CheckCircle class="h-5 w-5 text-green-600" />
        )} Analysis Complete
      </CardTitle>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="text-center p-6 bg-muted rounded-lg">
        <div class="text-3xl font-bold mb-2">{analysisResult.confidence}%</div>
        <div class="text-lg mb-2">
          {analysisResult.isAI ? (
          <span class="text-red-600">AI Generated Content</span>
          ) : (
          <span class="text-green-600">Authentic Content</span>
          )}
        </div>
        <p class="text-sm text-muted-foreground">
          Confidence level based on {frameCount} frame analysis
        </p>
      </div>

      <div class="grid grid-cols-2 gap-2"></div>

      <Separator />

      <div class="space-y-2 text-sm text-muted-foreground">
        <p><strong>Analysis Details:</strong></p>
        <p>• Frames analyzed: {frameCount}</p>
        <p>• Detection model: AI-Video-Detector v2.1</p>
        <p>• Processing time: ~{Math.ceil(parseInt(frameCount) * 0.8)}s</p>
      </div>

      <Button onClick="{resetProcess}" class="w-full" variant="outline">
        Analyze Another Video
      </Button>
    </CardContent>
  </Card>
</template>
