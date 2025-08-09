import type { IVideoFrame } from "@/types";
import { defineStore } from "pinia";
import { ref } from "vue";

export const useFramesStore = defineStore("frames", () => {
  const frames = ref<IVideoFrame[]>([]);


  const setFrames = (capturedFrames: IVideoFrame[]) => {
    frames.value = capturedFrames;
  };

  const clearFrames = () => {
    frames.value = [];
  };
  const addFrame = (frame: IVideoFrame) => {
    frames.value.push(frame);
  };

  return { frames, setFrames, clearFrames, addFrame };
});
