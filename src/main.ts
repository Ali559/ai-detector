/*
 * Copyright (C) 2025 Ali Barznji
 * This file is part of MyProject.
 *
 * MyProject is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 */

import App from './popup/App.vue'
import './assets/index.css'
import router from './router'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
const app = createApp(App).use(createPinia()).use(router)

app.mount('#app')
