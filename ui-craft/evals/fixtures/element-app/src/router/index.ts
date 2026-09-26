import { createRouter, createWebHashHistory, RouteRecordRaw } from 'vue-router';
import Layout from '@/layout/index.vue';

const routes: RouteRecordRaw[] = [
  { path: '/login', component: () => import('@/views/login') },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import(/* webpackChunkName: "dashboard" */ '@/views/dashboard.vue') },
    ],
  },
];

export default createRouter({ history: createWebHashHistory(), routes });
