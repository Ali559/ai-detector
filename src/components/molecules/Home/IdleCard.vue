<script setup lang="ts">
import Button from '@/components/ui/button/Button.vue'
import Card from '@/components/ui/card/Card.vue'
import CardContent from '@/components/ui/card/CardContent.vue'
import CardDescription from '@/components/ui/card/CardDescription.vue'
import CardHeader from '@/components/ui/card/CardHeader.vue'
import CardTitle from '@/components/ui/card/CardTitle.vue'
import Select from '@/components/ui/select/Select.vue'
import SelectContent from '@/components/ui/select/SelectContent.vue'
import SelectItem from '@/components/ui/select/SelectItem.vue'
import SelectTrigger from '@/components/ui/select/SelectTrigger.vue'
import SelectValue from '@/components/ui/select/SelectValue.vue'
import { Play } from 'lucide-vue-next'
import { ref } from 'vue'

const frameCount = ref<'1' | '2' | '3' | '4' | '5' | '6' | '7' | '8' | '9' | '10'>('5')
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Extract Video Frames</CardTitle>
      <CardDescription>
        Select how many frames to extract from the active tab's video player
      </CardDescription>
    </CardHeader>
    <CardContent class="space-y-4 p-4">
      <div class="space-y-2">
        <label class="block">Number of frames (1-10)</label>
        <Select v-model="frameCount">
          <SelectTrigger class="w-full">
            <SelectValue placeholder="Select number of frames" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="i in 10" :key="i" :value="(i + 1).toString()"
              >{{ i }} frame{{ i !== 1 ? 's' : '' }}</SelectItem
            >
          </SelectContent>
        </Select>
      </div>
      <Button class="w-full">
        <Play class="h-4 w-4 mr-2" />
        Start Extraction
      </Button>
    </CardContent>
  </Card>
</template>
