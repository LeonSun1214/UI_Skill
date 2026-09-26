import { Routes } from '@angular/router';
import { SettingsComponent } from './settings.component';

export const SETTINGS_ROUTES: Routes = [
  { path: '', component: SettingsComponent, title: 'Settings' },
  { path: 'profile', loadComponent: () => import('./profile/profile').then((m) => m.Profile) },
];
