<script setup lang="ts">
import { ref } from 'vue'
import LoaderIcon from './components/atoms/icons/LoaderIcon.vue'

const loading = ref<boolean>(false)
const sendMessage = (message: string) => {
  chrome.runtime.sendMessage({ message })
  loading.value = true
}
</script>

<template>
  <div class="container">
    <h1 class="header_title">AI Video Detector</h1>
    <LoaderIcon class="loader_icon" v-if="loading" />

    <div class="button_container">
      <button class="btn_action" @click='()=> sendMessage('START_DETECTION')'>Start</button>
      <button class="btn_action">Stop</button>
    </div>
  </div>
</template>

<style scoped>
.container {
  height: 700px;
  width: 500px;
  padding: 1.5rem;
  .header_title {
    font-size: 2rem;
    text-align: center;
    margin-bottom: 2rem;
  }

  .loader_icon {
    margin-inline: auto;
    display: block;
  }
  .button_container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    position: fixed;
    bottom: 20px;
    padding-inline: 2rem;
    left: 0;
    right: 0;
    width: 100%;
    margin-inline: auto;
  }
  .btn_action {
    background-color: #21aab4;
    color: #fff;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    cursor: pointer;
    outline: none;
    border: none;
    width: 100%;
    &:hover {
      background-color: #1a8b94;
    }
  }
}
</style>
