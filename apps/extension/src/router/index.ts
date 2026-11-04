import { getToken } from '@/lib/api'
import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../Views/HomeView.vue'),
  },
  {
    path: '/auth',
    name: 'Auth',
    component: () => import('../Views/AuthView.vue'),
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.name !== 'Auth' && !(await getToken())) return { name: 'Auth' }
})

export default router
