import { createRouter, createWebHistory } from 'vue-router';

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../views/Home.vue') },
    { path: '/settings', component: () => import('../views/Settings.vue') },
  ],
});
