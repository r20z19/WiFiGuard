import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('../views/Alerts.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/Devices.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/whitelist',
    name: 'Whitelist',
    component: () => import('../views/Whitelist.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/blacklist',
    name: 'Blacklist',
    component: () => import('../views/Blacklist.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/email',
    name: 'Email',
    component: () => import('../views/Email.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const isFirstLogin = localStorage.getItem('isFirstLogin') !== 'false'

  // Protected route without token → force login
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }

  // Protected route with token but password not yet changed → force password change
  if (to.meta.requiresAuth && token && isFirstLogin) {
    next('/login')
    return
  }

  // Already on login page with valid token and password changed → skip login
  if (to.path === '/login' && token && !isFirstLogin) {
    next('/')
    return
  }

  next()
})

export default router
