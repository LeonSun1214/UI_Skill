import type { RouteObject } from 'react-router';
import { lazy, Suspense } from 'react';
import { Outlet } from 'react-router';

import { DashboardLayout } from 'src/layouts/dashboard';
import { RequireAuth } from 'src/auth/require-auth';

export const DashboardPage = lazy(() => import('src/pages/dashboard'));
export const SettingsPage = lazy(() => import('src/pages/settings'));
export const SignInPage = lazy(() => import('src/pages/sign-in'));

export const routesSection: RouteObject[] = [
  {
    element: (
      <RequireAuth>
        <DashboardLayout>
          <Suspense>
            <Outlet />
          </Suspense>
        </DashboardLayout>
      </RequireAuth>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
  { path: 'sign-in', element: <SignInPage /> },
];
