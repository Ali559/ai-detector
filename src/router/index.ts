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

router.beforeEach((to, from, next) => {
  const isLoggedIn = Boolean(localStorage.getItem('token'))
  if (to.name !== 'Auth' && !isLoggedIn) {
    next({ name: 'Auth' })
    return
  }
  next()
})

export default router
