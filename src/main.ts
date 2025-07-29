import App from './popup/App.vue'
import './assets/main.css'
import router from './router'
import { createApp } from 'vue'
import { createPinia } from 'pinia'

const app = createApp(App).use(createPinia()).use(router)

app.mount('#app')
