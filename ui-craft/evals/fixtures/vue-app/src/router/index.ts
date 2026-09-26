import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
    { path: '/reports', name: 'reports', component: () => import('../views/ReportsView.vue') },
    { path: '/old-settings', redirect: '/settings' },
  ],
})
