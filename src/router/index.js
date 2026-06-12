import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('../views/Alerts.vue')
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('../views/History.vue')
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/Devices.vue')
  },
  {
    path: '/whitelist',
    name: 'Whitelist',
    component: () => import('../views/Whitelist.vue')
  },
  {
    path: '/blacklist',
    name: 'Blacklist',
    component: () => import('../views/Blacklist.vue')
  },
  {
    path: '/email',
    name: 'Email',
    component: () => import('../views/Email.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
