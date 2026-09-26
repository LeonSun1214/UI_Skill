import { Routes } from '@angular/router';
import { ShellComponent } from './shell/shell.component';
import { Login } from './pages/login/login';
import { NotFound } from './pages/not-found/not-found';
import { authGuard } from './auth/auth-guard';

export const routes: Routes = [
  { path: 'login', component: Login, title: 'Sign in' },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        title: 'Dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'orders',
        title: 'Orders',
        loadComponent: () => import('./pages/orders/orders.component').then((m) => m.OrdersComponent),
      },
      {
        path: 'settings',
        loadChildren: () => import('./pages/settings/settings.routes').then((m) => m.SETTINGS_ROUTES),
      },
      { path: 'reports', loadChildren: () => import('./reports/reports.routes') },
      { path: 'admin', loadChildren: () => import('./admin/admin.module').then((m) => m.AdminModule) },
    ],
  },
  { path: '**', component: NotFound },
];
