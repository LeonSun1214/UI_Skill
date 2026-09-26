import { Routes } from '@angular/router';

export default [
  { path: '', title: 'Reports', loadComponent: () => import('./reports-page').then((m) => m.ReportsPage) },
] satisfies Routes;
