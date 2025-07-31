import type { CapturedFrame } from "@/types";
import { defineStore } from "pinia";
import { ref } from "vue";

export const useFramesStore = defineStore("frames", () => {
  const frames = ref<CapturedFrame[]>([]);


  const setFrames = (capturedFrames: CapturedFrame[]) => {
    frames.value = capturedFrames;
  };

  const clearFrames = () => {
    frames.value = [];
  };
  const addFrame = (frame: CapturedFrame) => {
    frames.value.push(frame);
  };

  return { frames, setFrames, clearFrames, addFrame };
});
